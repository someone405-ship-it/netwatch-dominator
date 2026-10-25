# NetWatch Dominator

Live WiFi / hotspot / router device monitor with connection history, permanent MAC ban/unban, remote payload delivery, device control, crash/popup payloads, and a pile of extra network tools.

## Features

- Live device discovery (ARP + active scan)
- Connection history with timestamps, MAC, IP, hostname, vendor, first/last seen
- Permanent ban list (MAC) — survives restarts, blocks until unban
- Unban any time
- Payload generator: crash loops, random popups, reverse shell skeleton, keylogger skeleton, screen spam
- One-click "send" payload to target (copies to clipboard / generates dropper)
- Device type / OS guess
- OUI vendor lookup
- Bandwidth estimate per device
- Port scan on selected target
- Hostname resolve + reverse DNS
- Export history / ban list as JSON/CSV
- Auto-refresh live view
- Dark / light theme toggle
- Alert on new device
- Deauth option (requires monitor mode + scapy)
- Local hotspot mode detection
- Router admin quick-link helper
- Packet sniff summary (optional)
- Blacklist import/export
- Multi-adapter support

## Requirements

- Python 3.9+
- Admin / root for raw sockets and ARP
- Windows / Linux / macOS (scapy + netifaces)

```bash
pip install -r requirements.txt
```

On Windows run as Administrator. On Linux `sudo`.

## Run

```bash
python main.py
```

## Notes

- Ban is enforced via ARP poison + local firewall rules when possible. For true permanent router-level ban you still need to push the MAC into the router's MAC filter (the app shows the command / steps).
- Payloads are generated as standalone .py / .bat / .ps1. Delivery is manual or via the built-in dropper generator.
- Absolute olliE energy.

Repo: https://github.com/someone405-ship-it/netwatch-dominator
