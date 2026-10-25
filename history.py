#!/usr/bin/env python3
"""Connection history with model"""

import json
import time
import csv
from pathlib import Path
from typing import List, Dict

class HistoryDB:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: Dict[str, dict] = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.records = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.records = {}

    def save(self):
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def record(self, device):
        mac = device.mac.lower()
        now = time.time()
        model = getattr(device, "model", None) or getattr(device, "vendor", "")
        if mac not in self.records:
            self.records[mac] = {
                "mac": mac, "ip": device.ip, "hostname": device.hostname,
                "model": model,
                "device_type": getattr(device, "device_type", "unknown"),
                "os_guess": getattr(device, "os_guess", ""),
                "first_seen": now, "last_seen": now, "seen_count": 1,
                "ips": [device.ip],
            }
        else:
            r = self.records[mac]
            r["last_seen"] = now
            r["seen_count"] = r.get("seen_count", 0) + 1
            r["ip"] = device.ip
            r["hostname"] = device.hostname or r.get("hostname", "")
            r["model"] = model or r.get("model", "")
            if device.ip not in r.get("ips", []):
                r.setdefault("ips", []).append(device.ip)
        self.save()

    def all(self) -> List[dict]:
        return sorted(self.records.values(), key=lambda x: x.get("last_seen", 0), reverse=True)

    def by_mac(self, mac: str):
        return self.records.get(mac.lower())

    def export_csv(self, path: Path):
        rows = self.all()
        if not rows: return
        keys = list(rows[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                flat = {k: (",".join(v) if isinstance(v, list) else v) for k, v in r.items()}
                w.writerow(flat)
