#!/usr/bin/env python3
"""NetWatch Dominator — overpowered entry"""

from pathlib import Path
from scanner import NetworkScanner
from ban_manager import BanManager
from history import HistoryDB
from payload import PayloadFactory
from gui import DominatorGUI

def main():
    base = Path(__file__).parent
    (base / "data").mkdir(exist_ok=True)
    (base / "payloads").mkdir(exist_ok=True)
    (base / "payloads" / "control").mkdir(exist_ok=True)
    (base / "payloads" / "destroy").mkdir(exist_ok=True)

    hist = HistoryDB(base / "data" / "history.json")
    bans = BanManager(base / "data" / "bans.json")
    scanner = NetworkScanner(hist, bans)
    payloads = PayloadFactory(base / "payloads")

    app = DominatorGUI(scanner, bans, hist, payloads)
    app.run()

if __name__ == "__main__":
    main()
