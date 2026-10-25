#!/usr/bin/env python3
"""Permanent MAC ban with real enforcement + always-available unban"""

import json
import time
import sys
import subprocess
import threading
from pathlib import Path
from typing import Dict, List

class BanManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.bans: Dict[str, dict] = {}
        self._poison_thread = None
        self._poison_stop = threading.Event()
        self.load()
        # re-apply blocks on startup
        for mac, entry in list(self.bans.items()):
            if entry.get("active"):
                self._apply_local_block(mac)
        self._start_poison_loop()

    def load(self):
        if self.path.exists():
            try:
                self.bans = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.bans = {}

    def save(self):
        try:
            self.path.write_text(json.dumps(self.bans, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _norm(self, mac: str) -> str:
        return mac.lower().replace("-", ":").strip()

    def ban(self, mac: str, reason: str = "", ip: str = "", hostname: str = ""):
        mac = self._norm(mac)
        self.bans[mac] = {
            "mac": mac,
            "reason": reason or "manual",
            "ip": ip,
            "hostname": hostname,
            "banned_at": time.time(),
            "active": True,
        }
        self.save()
        self._apply_local_block(mac)
        return True

    def unban(self, mac: str):
        mac = self._norm(mac)
        if mac in self.bans:
            self.bans[mac]["active"] = False
            self.bans[mac]["unbanned_at"] = time.time()
            self.save()
            self._remove_local_block(mac)
            return True
        # still try remove rules even if not in db
        self._remove_local_block(mac)
        return False

    def is_banned(self, mac: str) -> bool:
        mac = self._norm(mac)
        entry = self.bans.get(mac)
        return bool(entry and entry.get("active"))

    def list_bans(self) -> List[dict]:
        return [v for v in self.bans.values() if v.get("active")]

    def list_all(self) -> List[dict]:
        return list(self.bans.values())

    def _apply_local_block(self, mac):
        mac = self._norm(mac)
        try:
            if sys.platform.startswith("win"):
                # Windows: netsh + firewall rule by description (MAC filter limited)
                # Drop via ARP poison is primary; also try route blackhole if IP known
                entry = self.bans.get(mac) or {}
                ip = entry.get("ip")
                if ip:
                    subprocess.run(
                        f'netsh interface ipv4 add route {ip}/32 0.0.0.0 metric=1 store=persistent',
                        shell=True, capture_output=True
                    )
                    subprocess.run(
                        f'netsh advfirewall firewall add rule name="NWBan_{mac.replace(":","")}" dir=out action=block remoteip={ip}',
                        shell=True, capture_output=True
                    )
                    subprocess.run(
                        f'netsh advfirewall firewall add rule name="NWBanIn_{mac.replace(":","")}" dir=in action=block remoteip={ip}',
                        shell=True, capture_output=True
                    )
            else:
                # Linux: iptables MAC match + ip neighbor
                for chain in ("INPUT", "FORWARD", "OUTPUT"):
                    subprocess.run(
                        ["iptables", "-C", chain, "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                        capture_output=True
                    )
                    # only add if not present
                    r = subprocess.run(
                        ["iptables", "-C", chain, "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                        capture_output=True
                    )
                    if r.returncode != 0:
                        subprocess.run(
                            ["iptables", "-I", chain, "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                            capture_output=True
                        )
                entry = self.bans.get(mac) or {}
                ip = entry.get("ip")
                if ip:
                    subprocess.run(["ip", "route", "add", "blackhole", ip], capture_output=True)
                    subprocess.run(["iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True)
                    subprocess.run(["iptables", "-I", "OUTPUT", "-d", ip, "-j", "DROP"], capture_output=True)
        except Exception:
            pass

    def _remove_local_block(self, mac):
        mac = self._norm(mac)
        try:
            if sys.platform.startswith("win"):
                entry = self.bans.get(mac) or {}
                ip = entry.get("ip")
                tag = mac.replace(":", "")
                subprocess.run(f'netsh advfirewall firewall delete rule name="NWBan_{tag}"', shell=True, capture_output=True)
                subprocess.run(f'netsh advfirewall firewall delete rule name="NWBanIn_{tag}"', shell=True, capture_output=True)
                if ip:
                    subprocess.run(f'netsh interface ipv4 delete route {ip}/32', shell=True, capture_output=True)
            else:
                for chain in ("INPUT", "FORWARD", "OUTPUT"):
                    subprocess.run(
                        ["iptables", "-D", chain, "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                        capture_output=True
                    )
                entry = self.bans.get(mac) or {}
                ip = entry.get("ip")
                if ip:
                    subprocess.run(["ip", "route", "del", "blackhole", ip], capture_output=True)
                    subprocess.run(["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True)
                    subprocess.run(["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"], capture_output=True)
        except Exception:
            pass

    def _start_poison_loop(self):
        """Continuous ARP reply poison against banned MACs so they can't talk on LAN."""
        if self._poison_thread and self._poison_thread.is_alive():
            return
        self._poison_stop.clear()
        def loop():
            try:
                from scapy.all import Ether, ARP, sendp, conf
                conf.verb = 0
            except Exception:
                return
            while not self._poison_stop.is_set():
                active = self.list_bans()
                for entry in active:
                    mac = entry.get("mac")
                    ip = entry.get("ip")
                    if not mac or not ip:
                        continue
                    try:
                        # tell the victim gateway is at fake mac, and tell network victim is at fake
                        pkt1 = Ether(dst=mac)/ARP(op=2, pdst=ip, psrc="0.0.0.0", hwdst=mac)
                        pkt2 = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=2, pdst=ip, psrc=ip, hwsrc="de:ad:be:ef:00:01")
                        sendp([pkt1, pkt2], verbose=0, inter=0.05)
                    except Exception:
                        pass
                self._poison_stop.wait(2.0)
        self._poison_thread = threading.Thread(target=loop, daemon=True)
        self._poison_thread.start()

    def stop_poison(self):
        self._poison_stop.set()

    def export_json(self, path: Path):
        path.write_text(json.dumps(self.bans, indent=2), encoding="utf-8")

    def import_json(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.bans.update(data)
        self.save()
        for mac, e in data.items():
            if e.get("active"):
                self._apply_local_block(mac)
