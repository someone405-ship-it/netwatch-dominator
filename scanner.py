#!/usr/bin/env python3
"""Network discovery, live view, traffic hints"""

import socket
import struct
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import netifaces
import psutil

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
        # simple /24 assumption for most home nets
        parts = self.local_ip.split(".")
        return ".".join(parts[:3]) + ".0/24"

    def _resolve_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def _guess_type(self, mac, hostname):
        h = (hostname or "").lower()
        if any(x in h for x in ("iphone", "android", "pixel", "galaxy")):
            return "mobile"
        if any(x in h for x in ("macbook", "imac", "pc-", "desktop", "laptop")):
            return "computer"
        if any(x in h for x in ("tv", "roku", "chromecast", "firestick")):
            return "media"
        if any(x in h for x in ("printer", "hp-", "epson")):
            return "printer"
        return "unknown"

    def _vendor(self, mac):
        prefix = mac.upper().replace(":", "")[:6]
        if prefix in self._oui_cache:
            return self._oui_cache[prefix]
        # minimal offline OUI hints
        known = {
            "001A11": "Google",
            "F0D1A9": "Apple",
            "3C5AB4": "Google",
            "B827EB": "Raspberry Pi",
            "DC:A6:32": "Raspberry Pi",
            "00:50:56": "VMware",
            "08:00:27": "VirtualBox",
        }
        for k, v in known.items():
            if prefix.startswith(k.replace(":", "")):
                self._oui_cache[prefix] = v
                return v
        self._oui_cache[prefix] = "unknown"
        return "unknown"

    def arp_scan(self):
        found = {}
        if not SCAPY:
            # fallback: ping sweep + arp table
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
            print("[scanner] arp error:", e)
        return found

    def _fallback_scan(self):
        # pure python arp table + ping
        found = {}
        now = time.time()
        # read system arp
        try:
            if sys.platform.startswith("win"):
                import subprocess
                out = subprocess.check_output("arp -a", shell=True, text=True)
                for line in out.splitlines():
                    if "dynamic" in line.lower() or "static" in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[0]
                            mac = parts[1].replace("-", ":").lower()
                            if mac.count(":") == 5:
                                host = self._resolve_hostname(ip)
                                d = Device(ip=ip, mac=mac, hostname=host,
                                           first_seen=now, last_seen=now)
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
                            d = Device(ip=ip, mac=mac, hostname=host,
                                       first_seen=now, last_seen=now)
                            found[mac] = d
                            self.history.record(d)
        except Exception:
            pass
        return found

    def port_scan(self, ip, ports=None):
        if ports is None:
            ports = [21, 22, 23, 80, 443, 445, 3389, 8080, 8443]
        open_ports = []
        def check(p):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.4)
                if s.connect_ex((ip, p)) == 0:
                    open_ports.append(p)
                s.close()
            except Exception:
                pass
        with ThreadPoolExecutor(max_workers=20) as ex:
            list(ex.map(check, ports))
        return sorted(open_ports)

    def start_live(self, interval=5.0):
        self.running = True
        def loop():
            while self.running:
                found = self.arp_scan()
                with self.lock:
                    # mark offline
                    for mac, d in list(self.devices.items()):
                        if mac not in found:
                            d.is_online = False
                    # update / add
                    for mac, d in found.items():
                        if mac in self.devices:
                            old = self.devices[mac]
                            d.first_seen = old.first_seen
                            d.bytes_sent = old.bytes_sent
                            d.bytes_recv = old.bytes_recv
                        self.devices[mac] = d
                time.sleep(interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def stop_live(self):
        self.running = False

    def get_live(self):
        with self.lock:
            return list(self.devices.values())

    def deauth(self, target_mac, count=5):
        """Requires monitor mode + scapy. Educational / lab only."""
        if not SCAPY:
            return False, "scapy missing"
        try:
            from scapy.all import Dot11, Dot11Deauth, RadioTap, sendp
            # needs monitor iface — user must set it
            pkt = RadioTap() / Dot11(addr1=target_mac, addr2="ff:ff:ff:ff:ff:ff",
                                     addr3="ff:ff:ff:ff:ff:ff") / Dot11Deauth()
            sendp(pkt, count=count, inter=0.1, verbose=0)
            return True, "deauth sent"
        except Exception as e:
            return False, str(e)
