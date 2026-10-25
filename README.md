# NetWatch Dominator — Expert / Hardened Edition

Full overpowered local network domination suite with **self-protection** and **device model** fingerprinting.

## Device intelligence
Live table now shows **MODEL** (not just vendor):
- OUI → model family map (iPhone, Galaxy, Pixel, MacBook, Echo, Pi, VMs…)
- Hostname regex fingerprinting
- OS guess column

## App self-security (hard to attack the tool itself)
- PBKDF2-HMAC-SHA256 + Fernet encrypted auth blob
- HMAC-SHA256 integrity manifest over core modules
- Anti-debug: Windows `IsDebuggerPresent` / `CheckRemoteDebuggerPresent`, Linux `TracerPid` + `ptrace`
- Background watchdog — process exits on debugger attach or integrity break
- Linux `PR_SET_DUMPABLE=0`
- Security tab: check integrity, re-seal, anti-debug test
- Default lab password: `dominator` (change in `main.py`)

## Control (real)
Full RAT + listener + keylogger + Android RAT skeleton  
Commands: shell, file get/put, screenshot, persist, ps, sysinfo, kill

## Destroy (real impact sim)
Full combo (lock + popups + mem/cpu + ransom-sim + BSOD attempt), wiper sim, Android destroy

## Network
Live ARP, history, permanent MAC ban, port scan, deauth, export, dark UI, .exe build

```bash
pip install -r requirements.txt
python main.py
python build_exe.py
```

Figma: https://www.figma.com/design/4utep1StwcVV22QmJ9pBYe  
Repo: https://github.com/someone405-ship-it/netwatch-dominator
