#!/usr/bin/env python3
"""NetWatch Dominator — hardened entry, bugfixed"""

import sys
from pathlib import Path

def main():
    base = Path(__file__).parent
    data = base / "data"
    data.mkdir(exist_ok=True)
    (base / "payloads" / "control").mkdir(parents=True, exist_ok=True)
    (base / "payloads" / "destroy").mkdir(parents=True, exist_ok=True)

    from security import AppSecurity
    from scanner import NetworkScanner
    from ban_manager import BanManager
    from history import HistoryDB
    from payload import PayloadFactory
    from gui import DominatorGUI

    sec = AppSecurity(data)
    if not (data / ".auth").exists():
        try:
            sec.set_password("dominator")
        except Exception:
            pass
    else:
        sec.authenticate("dominator")

    core_files = [base / f for f in ("main.py", "scanner.py", "payload.py", "gui.py", "security.py")]
    if not (data / ".integrity").exists():
        try:
            sec.seal_integrity(core_files)
        except Exception:
            pass
    try:
        sec.harden_process()
        sec.watchdog(12.0)
    except Exception:
        pass

    hist = HistoryDB(data / "history.json")
    bans = BanManager(data / "bans.json")
    scanner = NetworkScanner(hist, bans)
    payloads = PayloadFactory(base / "payloads")

    app = DominatorGUI(scanner, bans, hist, payloads, sec)
    app.run()

if __name__ == "__main__":
    main()
