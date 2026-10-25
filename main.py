#!/usr/bin/env python3
"""
NetWatch Dominator - main entry
Live monitor + ban + payload suite
"""

import sys
import os
import threading
import time
from pathlib import Path

# local modules
from scanner import NetworkScanner
from ban_manager import BanManager
from history import HistoryDB
from payload import PayloadFactory
from gui import DominatorGUI

def main():
    base = Path(__file__).parent
    hist = HistoryDB(base / "data" / "history.json")
    bans = BanManager(base / "data" / "bans.json")
    scanner = NetworkScanner(hist, bans)
    payloads = PayloadFactory(base / "payloads")

    # ensure dirs
    (base / "data").mkdir(exist_ok=True)
    (base / "payloads").mkdir(exist_ok=True)

    app = DominatorGUI(scanner, bans, hist, payloads)
    app.run()

if __name__ == "__main__":
    main()
