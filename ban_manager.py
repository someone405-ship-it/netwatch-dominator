#!/usr/bin/env python3
"""Permanent MAC ban / unban with persistence"""

import json
import time
from pathlib import Path
from typing import Dict, List

class BanManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.bans: Dict[str, dict] = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.bans = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.bans = {}

    def save(self):
        self.path.write_text(json.dumps(self.bans, indent=2), encoding="utf-8")

    def ban(self, mac: str, reason: str = "", ip: str = "", hostname: str = ""):
        mac = mac.lower().replace("-", ":")
        self.bans[mac] = {
            "mac": mac,
            "reason": reason,
            "ip": ip,
            "hostname": hostname,
            "banned_at": time.time(),
            "active": True
        }
        self.save()
        self._apply_local_block(mac)
        return True

    def unban(self, mac: str):
        mac = mac.lower().replace("-", ":")
        if mac in self.bans:
            self.bans[mac]["active"] = False
            self.bans[mac]["unbanned_at"] = time.time()
            self.save()
            self._remove_local_block(mac)
            return True
        return False

    def is_banned(self, mac: str) -> bool:
        mac = mac.lower().replace("-", ":")
        entry = self.bans.get(mac)
        return bool(entry and entry.get("active"))

    def list_bans(self) -> List[dict]:
        return [v for v in self.bans.values() if v.get("active")]

    def list_all(self) -> List[dict]:
        return list(self.bans.values())

    def _apply_local_block(self, mac):
        """Best-effort local firewall + ARP poison note"""
        import sys, subprocess
        try:
            if sys.platform.startswith("win"):
                # Windows Firewall outbound block by MAC is limited;
                # we add a note and use netsh if possible
                pass
            else:
                # Linux: iptables / nft mac match if available
                subprocess.run(
                    ["iptables", "-A", "INPUT", "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                    capture_output=True
                )
                subprocess.run(
                    ["iptables", "-A", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                    capture_output=True
                )
        except Exception:
            pass

    def _remove_local_block(self, mac):
        import sys, subprocess
        try:
            if not sys.platform.startswith("win"):
                subprocess.run(
                    ["iptables", "-D", "INPUT", "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                    capture_output=True
                )
                subprocess.run(
                    ["iptables", "-D", "FORWARD", "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                    capture_output=True
                )
        except Exception:
            pass

    def export_json(self, path: Path):
        path.write_text(json.dumps(self.bans, indent=2), encoding="utf-8")

    def import_json(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.bans.update(data)
        self.save()
