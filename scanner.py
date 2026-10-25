#!/usr/bin/env python3
"""Network discovery — upgraded"""

import socket
import time
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from typing import Dict, List
import netifaces

try:
    from scapy.all import ARP, Ether, srp, conf, get_if_list, get_if_addr
    SCAPY = True
except ImportError:
    SCAPY = False

@dataclass
class Device:
    ip: str
    mac: str
    hostname: str = ""
    vendor: str = ""
    first_seen: float = 0.0
    last_seen: float = 0.0
    is_online: bool = True
    device_type: str = "unknown"
    bytes_sent: int = 0
    bytes_recv: int = 0
    ports: List[int] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

class NetworkScanner:
    def __init__(self, history, ban_manager):
        self.history = history
        self.bans = ban_manager
        self.devices: Dict[str, Device] = {}
        self.lock = threading.Lock()
        self.running = False
        self.iface = self._pick_iface()
        self.local_ip = self._get_local_ip()
        self.subnet = self._get_subnet()
        self._oui_cache = {}

    def _pick_iface(self):
        if SCAPY:
            for i in get_if_list():
                try:
                    addr = get_if_addr(i)
                    if addr and not addr.startswith("127."):
                        return i
                except Exception:
                    pass
        return None

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _get_subnet(self):
        parts = self.local_ip.split(".")
        return ".".join(parts[:3]) + ".0/24"

    def _resolve_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def _guess_type(self, mac, hostname):
        h = (hostname or "").lower()
        if any(x in h for x in ("iphone", "android", "pixel", "galaxy", "oneplus")):
            return "mobile"
        if any(x in h for x in ("macbook", "imac", "pc-", "desktop", "laptop", "surface")):
            return "computer"
        if any(x in h for x in ("tv", "roku", "chromecast", "firestick", "shield")):
            return "media"
        if any(x in h for x in ("printer", "hp-", "epson", "canon")):
            return "printer"
        return "unknown"

    def _vendor(self, mac):
        prefix = mac.upper().replace(":", "")[:6]
        if prefix in self._oui_cache:
            return self._oui_cache[prefix]
        known = {
            "001A11": "Google", "F0D1A9": "Apple", "3C5AB4": "Google",
            "B827EB": "RaspberryPi", "DCA632": "RaspberryPi",
            "005056": "VMware", "080027": "VirtualBox",
            "F4F5E8": "Google", "A4C138": "Xiaomi", "FCDBB3": "Samsung",
        }
        for k, v in known.items():
            if prefix.startswith(k):
                self._oui_cache[prefix] = v
                return v
        self._oui_cache[prefix] = "unknown"
        return "unknown"

    def arp_scan(self):
        found = {}
        if not SCAPY:
            return self._fallback_scan()
        try:
            conf.verb = 0
            ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=self.subnet),
                         timeout=2, iface=self.iface, inter=0.05, verbose=0)
            now = time.time()
            for snd, rcv in ans:
                ip = rcv.psrc
                mac = rcv.hwsrc.lower()
                if self.bans.is_banned(mac):
                    continue
                host = self._resolve_hostname(ip)
                vendor = self._vendor(mac)
                dtype = self._guess_type(mac, host)
                d = Device(ip=ip, mac=mac, hostname=host, vendor=vendor,
                           first_seen=now, last_seen=now, is_online=True,
                           device_type=dtype)
                found[mac] = d
                self.history.record(d)
        except Exception as e:
            print("[scanner]", e)
        return found

    def _fallback_scan(self):
        found = {}
        now = time.time()
        try:
            if sys.platform.startswith("win"):
                import subprocess
                out = subprocess.check_output("arp -a", shell=True, text=True, errors="ignore")
                for line in out.splitlines():
                    parts = line.split()
                    if len(parts) >= 2 and ("dynamic" in line.lower() or "static" in line.lower()):
                        ip, mac = parts[0], parts[1].replace("-", ":").lower()
                        if mac.count(":") == 5:
                            host = self._resolve_hostname(ip)
                            d = Device(ip=ip, mac=mac, hostname=host, first_seen=now, last_seen=now)
                            found[mac] = d
                            self.history.record(d)
            else:
                with open("/proc/net/arp") as f:
                    next(f)
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 4 and parts[2] != "0x0":
                            ip, mac = parts[0], parts[3]
                            host = self._resolve_hostname(ip)
                            d = Device(ip=ip, mac=mac, hostname=host, first_seen=now, last_seen=now)
                            found[mac] = d
                            self.history.record(d)
        except Exception:
            pass
        return found

    def port_scan(self, ip, ports=None):
        if ports is None:
            ports = [21,22,23,80,443,445,3389,8080,8443,5555,27042]
        open_ports = []
        def check(p):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.35)
                if s.connect_ex((ip, p)) == 0:
                    open_ports.append(p)
                s.close()
            except Exception:
                pass
        with ThreadPoolExecutor(max_workers=24) as ex:
            list(ex.map(check, ports))
        return sorted(open_ports)

    def start_live(self, interval=5.0):
        self.running = True
        def loop():
            while self.running:
                found = self.arp_scan()
                with self.lock:
                    for mac, d in list(self.devices.items()):
                        if mac not in found:
                            d.is_online = False
                    for mac, d in found.items():
                        if mac in self.devices:
                            old = self.devices[mac]
                            d.first_seen = old.first_seen
                        self.devices[mac] = d
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()

    def stop_live(self):
        self.running = False

    def get_live(self):
        with self.lock:
            return list(self.devices.values())

    def deauth(self, target_mac, count=5):
        if not SCAPY:
            return False, "scapy missing"
        try:
            from scapy.all import Dot11, Dot11Deauth, RadioTap, sendp
            pkt = RadioTap() / Dot11(addr1=target_mac, addr2="ff:ff:ff:ff:ff:ff",
                                     addr3="ff:ff:ff:ff:ff:ff") / Dot11Deauth()
            sendp(pkt, count=count, inter=0.1, verbose=0)
            return True, "deauth frames sent"
        except Exception as e:
            return False, str(e)
