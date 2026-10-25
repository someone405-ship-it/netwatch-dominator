#!/usr/bin/env python3
"""NetWatch Dominator — hardened entry"""

import sys
from pathlib import Path
from scanner import NetworkScanner
from ban_manager import BanManager
from history import HistoryDB
from payload import PayloadFactory
from security import AppSecurity
from gui import DominatorGUI

def main():
    base = Path(__file__).parent
    data = base / "data"
    data.mkdir(exist_ok=True)
    (base / "payloads" / "control").mkdir(parents=True, exist_ok=True)
    (base / "payloads" / "destroy").mkdir(parents=True, exist_ok=True)

    sec = AppSecurity(data)

    # first-run: optional password (skip if cryptography missing)
    if not (data / ".auth").exists():
        try:
            sec.set_password("dominator")  # default lab password — change it
        except Exception:
            pass
    else:
        # non-interactive: try default; GUI can re-prompt later if needed
        sec.authenticate("dominator")

    # integrity seal + watchdog
    core_files = [base / f for f in ("main.py", "scanner.py", "payload.py", "gui.py", "security.py")]
    if not (data / ".integrity").exists():
        sec.seal_integrity(core_files)
    ok, msg = sec.check_integrity(core_files)
    if not ok:
        print("[security] integrity fail:", msg)
        # still run in lab; production would exit
    if not sec.anti_debug():
        print("[security] debugger detected")
    sec.harden_process()
    sec.watchdog(10.0)

    hist = HistoryDB(data / "history.json")
    bans = BanManager(data / "bans.json")
    scanner = NetworkScanner(hist, bans)
    payloads = PayloadFactory(base / "payloads")

    app = DominatorGUI(scanner, bans, hist, payloads, sec)
    app.run()

if __name__ == "__main__":
    main()
