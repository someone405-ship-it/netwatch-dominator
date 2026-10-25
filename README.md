# NetWatch Dominator — Overpowered Edition

Live WiFi / hotspot / router domination suite.

See every connected device in real time. Permanent MAC ban. Two-mode payload system:

1. **CONTROL** — reverse shell, file system, keylog, screen, camera stub, persistence
2. **DESTROY** — crash loops, ransomware-style locker, wipe simulation, battery drain, UI lock, BSOD

Desktop GUI (CustomTkinter, pure dark theme). Builds to `.exe`. Payload generators also emit Android-oriented `.apk`-ready Python (Kivy/Buildozer) and pure `.py` droppers.

Figma dark UI reference: https://www.figma.com/design/4utep1StwcVV22QmJ9pBYe

## Core Capabilities

- Live ARP + active discovery, multi-adapter
- Full connection history with timestamps, multi-IP, vendor OUI, device type
- Permanent ban / unban (local firewall + ARP notes + export for router MAC filter)
- **Control payloads**: reverse shell (Windows/Linux), keylogger, screen capture loop, file browser skeleton, persistence installer, Android control skeleton
- **Destroy payloads**: memory bomb, fork bomb, BSOD trigger, fullscreen lock + message, random popup storm, ransomware-style file encryptor sim, battery/CPU melt, Android destroy skeleton
- One-click generate + dropper (.bat / .ps1 / .sh)
- Port scanner, deauth (lab), traffic estimate, hostname resolve
- Export CSV / JSON
- Auto live refresh, new-device alert sound hook
- Router admin launcher, local network map
- Dark cyber theme (black + neon red / cyan)
- PyInstaller build script → single .exe
- Android payload notes + Buildozer template

## Quick Start

```bash
git clone https://github.com/someone405-ship-it/netwatch-dominator
cd netwatch-dominator
pip install -r requirements.txt
python main.py
```

Run elevated (Admin / sudo) for full scan + ban power.

### Build Windows .exe

```bash
pip install pyinstaller
python build_exe.py
# output: dist/NetWatchDominator.exe
```

### Android payloads

Control and Destroy Android skeletons are generated as pure Python. Package with Buildozer / BeeWare / Chaquopy for real .apk. Template `android/buildozer.spec` included.

## Payload Modes

| Mode | Effect |
|------|--------|
| CONTROL | Remote shell, keylog, screen, file access, persistence |
| DESTROY | Crash, lock, wipe-sim, ransomware-style, melt |

Generate from the Payloads tab. Select target device → Generate Control or Generate Destroy → dropper created next to payload.

## Figma

Dark dashboard mock lives in the linked Figma file. Use it as visual source of truth for any future web/mobile port.

Repo: https://github.com/someone405-ship-it/netwatch-dominator
