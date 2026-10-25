#!/usr/bin/env python3
"""Build single-file NetWatchDominator.exe with PyInstaller"""

import subprocess
import sys
from pathlib import Path

def main():
    root = Path(__file__).parent
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "NetWatchDominator",
        "--add-data", f"data{os_sep()}.;data",
        str(root / "main.py"),
    ]
    # fix add-data separator
    import os
    sep = ";" if os.name == "nt" else ":"
    cmd[cmd.index("--add-data")+1] = f"data{sep}."
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=root)
    print("\nDone → dist/NetWatchDominator.exe")

def os_sep():
    import os
    return ";" if os.name == "nt" else ":"

if __name__ == "__main__":
    main()
