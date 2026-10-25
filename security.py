#!/usr/bin/env python3
"""App self-protection — anti-debug, integrity, auth, secure storage"""

import os
import sys
import hashlib
import hmac
import json
import time
import base64
import threading
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO = True
except ImportError:
    CRYPTO = False

class AppSecurity:
    def __init__(self, data_dir: Path, master_password: str = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = self.data_dir / ".auth"
        self.integrity_file = self.data_dir / ".integrity"
        self._fernet = None
        self._authenticated = False
        self._lock = threading.Lock()
        if master_password and CRYPTO:
            self._init_crypto(master_password)

    def _init_crypto(self, password: str):
        salt_path = self.data_dir / ".salt"
        if salt_path.exists():
            salt = salt_path.read_bytes()
        else:
            salt = os.urandom(16)
            salt_path.write_bytes(salt)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
        self._fernet = Fernet(key)

    def set_password(self, password: str):
        if not CRYPTO:
            return False
        self._init_crypto(password)
        token = self._fernet.encrypt(b"NETWATCH_OK")
        self.auth_file.write_bytes(token)
        self._authenticated = True
        return True

    def authenticate(self, password: str) -> bool:
        if not CRYPTO or not self.auth_file.exists():
            self._authenticated = True
            return True
        try:
            self._init_crypto(password)
            data = self._fernet.decrypt(self.auth_file.read_bytes())
            self._authenticated = data == b"NETWATCH_OK"
            return self._authenticated
        except Exception:
            self._authenticated = False
            return False

    @property
    def ok(self):
        return self._authenticated

    def encrypt_blob(self, data: bytes) -> bytes:
        if not self._fernet:
            return data
        return self._fernet.encrypt(data)

    def decrypt_blob(self, data: bytes) -> bytes:
        if not self._fernet:
            return data
        return self._fernet.decrypt(data)

    def secure_write(self, path: Path, obj):
        raw = json.dumps(obj, indent=2).encode("utf-8")
        path.write_bytes(self.encrypt_blob(raw))

    def secure_read(self, path: Path):
        if not path.exists():
            return {}
        raw = path.read_bytes()
        try:
            raw = self.decrypt_blob(raw)
        except Exception:
            pass
        return json.loads(raw.decode("utf-8"))

    # ── integrity ──

    def _file_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        if path.exists():
            h.update(path.read_bytes())
        return h.hexdigest()

    def seal_integrity(self, files: list):
        manifest = {}
        for f in files:
            p = Path(f)
            manifest[str(p)] = self._file_hash(p)
        secret = hashlib.sha256(b"netwatch-dominator-seal").digest()
        payload = json.dumps(manifest, sort_keys=True).encode()
        sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        self.integrity_file.write_text(json.dumps({"manifest": manifest, "sig": sig}), encoding="utf-8")

    def check_integrity(self, files: list) -> tuple:
        if not self.integrity_file.exists():
            return True, "no seal yet"
        try:
            data = json.loads(self.integrity_file.read_text(encoding="utf-8"))
            manifest = data["manifest"]
            sig = data["sig"]
            secret = hashlib.sha256(b"netwatch-dominator-seal").digest()
            payload = json.dumps(manifest, sort_keys=True).encode()
            expect = hmac.new(secret, payload, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expect):
                return False, "integrity signature mismatch"
            for f in files:
                p = Path(f)
                key = str(p)
                if key in manifest and manifest[key] != self._file_hash(p):
                    return False, f"tampered: {p.name}"
            return True, "ok"
        except Exception as e:
            return False, str(e)

    # ── anti-debug / anti-tamper ──

    def anti_debug(self) -> bool:
        """Best-effort debugger / tracer detection. Returns True if clean."""
        # linux tracerpid
        try:
            if sys.platform.startswith("linux"):
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith("TracerPid:"):
                            pid = int(line.split()[1])
                            if pid != 0:
                                return False
        except Exception:
            pass
        # windows IsDebuggerPresent
        try:
            if sys.platform.startswith("win"):
                import ctypes
                if ctypes.windll.kernel32.IsDebuggerPresent():
                    return False
                # CheckRemoteDebuggerPresent
                debugged = ctypes.c_bool(False)
                ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                    ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(debugged))
                if debugged.value:
                    return False
        except Exception:
            pass
        # ptrace self-test (linux)
        try:
            if sys.platform.startswith("linux"):
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                PTRACE_TRACEME = 0
                if libc.ptrace(PTRACE_TRACEME, 0, 0, 0) == -1:
                    return False
        except Exception:
            pass
        return True

    def watchdog(self, interval=8.0):
        """Background thread: exit if debugger attaches or integrity fails."""
        def loop():
            core = ["main.py", "scanner.py", "payload.py", "gui.py", "security.py"]
            while True:
                if not self.anti_debug():
                    os._exit(1)
                ok, _ = self.check_integrity(core)
                if not ok:
                    os._exit(1)
                time.sleep(interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def harden_process(self):
        """Hide from casual process lists where possible + restrict env."""
        try:
            if sys.platform.startswith("linux"):
                # prctl PR_SET_DUMPABLE = 0
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                PR_SET_DUMPABLE = 4
                libc.prctl(PR_SET_DUMPABLE, 0)
        except Exception:
            pass
