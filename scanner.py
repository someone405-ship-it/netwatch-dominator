#!/usr/bin/env python3
"""Advanced discovery — device MODEL focus, not just vendor"""

import socket
import time
import threading
import sys
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from typing import Dict, List

try:
    from scapy.all import ARP, Ether, srp, conf, get_if_list, get_if_addr
    SCAPY = True
except ImportError:
    SCAPY = False

# MAC OUI → likely model family (expert-style fingerprinting)
OUI_MODEL = {
    "F0D1A9": "Apple Device", "3C22FB": "Apple iPhone", "A4C361": "Apple Mac",
    "BC926B": "Apple iPhone", "D0C5F3": "Apple iPad", "F40616": "Apple Watch",
    "001A11": "Google Nest/Pixel", "F4F5E8": "Google Pixel", "3C5AB4": "Google Home",
    "A4C138": "Xiaomi Phone", "64CC2E": "Xiaomi Device", "FCDBB3": "Samsung Galaxy",
    "5C497D": "Samsung TV", "C0468D": "Samsung Device", "B827EB": "Raspberry Pi",
    "DCA632": "Raspberry Pi 4", "E45F01": "Raspberry Pi", "080027": "VirtualBox VM",
    "005056": "VMware VM", "000C29": "VMware VM", "00155D": "Hyper-V VM",
    "FCF136": "Samsung Galaxy", "9424B8": "Xiaomi Redmi", "28E31F": "Xiaomi Mi",
    "AC233F": "OnePlus Phone", "C0EE40": "Huawei Phone", "00E04C": "Realtek Adapter",
    "DC4427": "Amazon Echo/Fire", "68C63A": "Amazon Device", "F0D2F1": "Amazon Fire TV",
    "B0E235": "Xiaomi Device", "18D6C7": "TP-Link Device", "50C7BF": "TP-Link Router",
    "A0F3C1": "TP-Link Device", "CC46D8": "Cisco Device", "00A0C9": "Intel Device",
    "3C370C": "Samsung Device", "5C514F": "Intel Device",
}

HOSTNAME_MODEL = [
    (r"iphone", "iPhone"), (r"ipad", "iPad"), (r"macbook", "MacBook"),
    (r"imac", "iMac"), (r"android", "Android Phone"), (r"galaxy", "Samsung Galaxy"),
    (r"pixel", "Google Pixel"), (r"oneplus", "OnePlus"), (r"xiaomi|redmi|mi-", "Xiaomi Phone"),
    (r"huawei|honor", "Huawei Phone"), (r"desktop|pc-|laptop", "Windows PC"),
    (r"surface", "Microsoft Surface"), (r"raspberry|raspi", "Raspberry Pi"),
    (r"echo|alexa", "Amazon Echo"), (r"firestick|fire-tv", "Amazon Fire TV"),
    (r"chromecast", "Chromecast"), (r"roku", "Roku"), (r"smart-?tv|bravia|webos", "Smart TV"),
    (r"printer|hp-|epson|canon", "Printer"), (r"ipad", "iPad"),
    (r"watch", "Smartwatch"), (r"ipod", "iPod"),
]

@dataclass
class Device:
    ip: str
    mac: str
    hostname: str = ""
    model: str = "Unknown Device"
    vendor: str = ""
    first_seen: float = 0.0
    last_seen: float = 0.0
    is_online: bool = True
    device_type: str = "unknown"
    bytes_sent: int = 0
    bytes_recv: int = 0
    ports: List[int] = field(default_factory=list)
    os_guess: str = ""

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

    def _model_from_mac(self, mac: str) -> str:
        prefix = mac.upper().replace(":", "").replace("-", "")[:6]
        return OUI_MODEL.get(prefix, "")

    def _model_from_hostname(self, hostname: str) -> str:
        h = (hostname or "").lower()
        for pat, model in HOSTNAME_MODEL:
            if re.search(pat, h):
                return model
        return ""

    def _guess_model(self, mac, hostname):
        m1 = self._model_from_hostname(hostname)
        if m1:
            return m1
        m2 = self._model_from_mac(mac)
        if m2:
            return m2
        return "Unknown Device"

    def _guess_type(self, model, hostname):
        m = (model + " " + (hostname or "")).lower()
        if any(x in m for x in ("iphone", "android", "pixel", "galaxy", "oneplus", "xiaomi", "huawei", "phone")):
            return "mobile"
        if any(x in m for x in ("macbook", "imac", "pc", "laptop", "surface", "desktop", "windows")):
            return "computer"
        if any(x in m for x in ("tv", "roku", "chromecast", "fire", "echo", "shield")):
            return "media"
        if "print" in m:
            return "printer"
        if "raspberry" in m or "pi" in m:
            return "iot"
        if "vm" in m or "virtual" in m:
            return "virtual"
        return "unknown"

    def _os_guess(self, model, hostname, open_ports=None):
        m = (model + " " + (hostname or "")).lower()
        if any(x in m for x in ("iphone", "ipad", "macbook", "imac", "apple")):
            return "iOS/macOS"
        if any(x in m for x in ("android", "pixel", "galaxy", "xiaomi", "oneplus")):
            return "Android"
        if "windows" in m or "surface" in m or "pc-" in m:
            return "Windows"
        if open_ports:
            if 22 in open_ports and 445 not in open_ports:
                return "Linux/*nix"
            if 445 in open_ports or 3389 in open_ports:
                return "Windows"
        return ""

    def arp_scan(self):
        found = {}
        if not SCAPY:
            return self._fallback_scan()
        try:
            conf.verb = 0
            ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=self.subnet),
                         timeout=2.5, iface=self.iface, inter=0.04, verbose=0)
            now = time.time()
            for snd, rcv in ans:
                ip = rcv.psrc
                mac = rcv.hwsrc.lower()
                if self.bans.is_banned(mac):
                    continue
                host = self._resolve_hostname(ip)
                model = self._guess_model(mac, host)
                dtype = self._guess_type(model, host)
                os_g = self._os_guess(model, host)
                d = Device(ip=ip, mac=mac, hostname=host, model=model,
                           first_seen=now, last_seen=now, is_online=True,
                           device_type=dtype, os_guess=os_g)
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
                            model = self._guess_model(mac, host)
                            d = Device(ip=ip, mac=mac, hostname=host, model=model,
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
                            model = self._guess_model(mac, host)
                            d = Device(ip=ip, mac=mac, hostname=host, model=model,
                                       first_seen=now, last_seen=now)
                            found[mac] = d
                            self.history.record(d)
        except Exception:
            pass
        return found

    def port_scan(self, ip, ports=None):
        if ports is None:
            ports = [21,22,23,80,443,445,3389,8080,8443,5555,27042,5900,32400]
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
        with ThreadPoolExecutor(max_workers=28) as ex:
            list(ex.map(check, ports))
        return sorted(open_ports)

    def start_live(self, interval=4.0):
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
                            d.ports = old.ports
                        self.devices[mac] = d
                time.sleep(interval)
        threading.Thread(target=loop, daemon=True).start()

    def stop_live(self):
        self.running = False

    def get_live(self):
        with self.lock:
            return list(self.devices.values())

    def deauth(self, target_mac, count=8):
        if not SCAPY:
            return False, "scapy missing"
        try:
            from scapy.all import Dot11, Dot11Deauth, RadioTap, sendp
            pkt = RadioTap() / Dot11(addr1=target_mac, addr2="ff:ff:ff:ff:ff:ff",
                                     addr3="ff:ff:ff:ff:ff:ff") / Dot11Deauth()
            sendp(pkt, count=count, inter=0.08, verbose=0)
            return True, "deauth frames sent"
        except Exception as e:
            return False, str(e)
