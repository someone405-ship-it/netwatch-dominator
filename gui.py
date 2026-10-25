#!/usr/bin/env python3
"""Dark GUI — reliable ban/unban, model column, bugfixed"""

import customtkinter as ctk
import threading
from datetime import datetime
from tkinter import messagebox, filedialog
import webbrowser
from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class DominatorGUI:
    def __init__(self, scanner, bans, history, payloads, security=None):
        self.scanner = scanner
        self.bans = bans
        self.history = history
        self.payloads = payloads
        self.sec = security
        self.root = ctk.CTk()
        self.root.title("NetWatch Dominator")
        self.root.geometry("1280x800")
        self.root.configure(fg_color="#0a0a0c")
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self.root, fg_color="#0f0f14", height=52, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="NETWATCH DOMINATOR", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#00f0ff").pack(side="left", padx=16)
        ctk.CTkLabel(top, text="● HARDENED", text_color="#ff2a2a", font=ctk.CTkFont(size=12)).pack(side="left", padx=8)
        ctk.CTkButton(top, text="REFRESH", width=90, fg_color="#1a1a24", hover_color="#ff2a2a",
                      command=self.refresh).pack(side="right", padx=6, pady=8)
        ctk.CTkButton(top, text="START LIVE", width=100, fg_color="#1a1a24", hover_color="#00f0ff",
                      command=self.start_live).pack(side="right", padx=4, pady=8)
        ctk.CTkButton(top, text="STOP", width=70, fg_color="#1a1a24", hover_color="#666",
                      command=self.stop_live).pack(side="right", padx=4, pady=8)

        self.tabs = ctk.CTkTabview(self.root, fg_color="#0a0a0c",
                                   segmented_button_fg_color="#12121a",
                                   segmented_button_selected_color="#ff2a2a",
                                   segmented_button_selected_hover_color="#cc2222",
                                   text_color="#cccccc")
        self.tabs.pack(fill="both", expand=True, padx=8, pady=6)
        for name in ("Live", "History", "Bans", "Control", "Destroy", "Security", "Tools"):
            self.tabs.add(name)

        # LIVE
        self.live_box = ctk.CTkTextbox(self.tabs.tab("Live"), font=ctk.CTkFont(family="Consolas", size=13),
                                       fg_color="#0f0f14", text_color="#e0e0e0")
        self.live_box.pack(fill="both", expand=True, padx=4, pady=4)
        lb = ctk.CTkFrame(self.tabs.tab("Live"), fg_color="transparent")
        lb.pack(fill="x", pady=4)
        ctk.CTkButton(lb, text="BAN SELECTED", command=self.ban_selected,
                      fg_color="#ff2a2a", hover_color="#cc2222", width=130).pack(side="left", padx=4)
        ctk.CTkButton(lb, text="UNBAN SELECTED", command=self.unban_from_live,
                      fg_color="#1a1a24", hover_color="#00f0ff", width=130).pack(side="left", padx=4)
        ctk.CTkButton(lb, text="PORT SCAN", command=self.port_scan_selected,
                      fg_color="#1a1a24", width=110).pack(side="left", padx=4)
        ctk.CTkButton(lb, text="DEAUTH", command=self.deauth_selected,
                      fg_color="#1a1a24", width=90).pack(side="left", padx=4)
        ctk.CTkButton(lb, text="COPY MAC", command=self.copy_mac,
                      fg_color="#1a1a24", width=100).pack(side="left", padx=4)

        # HISTORY
        self.hist_box = ctk.CTkTextbox(self.tabs.tab("History"), font=ctk.CTkFont(family="Consolas", size=12), fg_color="#0f0f14")
        self.hist_box.pack(fill="both", expand=True, padx=4, pady=4)
        hb = ctk.CTkFrame(self.tabs.tab("History"), fg_color="transparent")
        hb.pack(fill="x")
        ctk.CTkButton(hb, text="RELOAD", command=self.load_history, fg_color="#1a1a24").pack(side="left", padx=4)
        ctk.CTkButton(hb, text="EXPORT CSV", command=self.export_hist, fg_color="#1a1a24").pack(side="left", padx=4)

        # BANS — always visible unban
        self.ban_box = ctk.CTkTextbox(self.tabs.tab("Bans"), font=ctk.CTkFont(family="Consolas", size=12), fg_color="#0f0f14")
        self.ban_box.pack(fill="both", expand=True, padx=4, pady=4)
        bb = ctk.CTkFrame(self.tabs.tab("Bans"), fg_color="transparent")
        bb.pack(fill="x")
        ctk.CTkButton(bb, text="REFRESH", command=self.load_bans, fg_color="#1a1a24").pack(side="left", padx=4)
        ctk.CTkButton(bb, text="UNBAN SELECTED", command=self.unban_selected,
                      fg_color="#00aa66", hover_color="#00cc77", width=140).pack(side="left", padx=4)
        ctk.CTkButton(bb, text="UNBAN ALL", command=self.unban_all,
                      fg_color="#1a1a24", width=110).pack(side="left", padx=4)
        ctk.CTkButton(bb, text="EXPORT", command=self.export_bans, fg_color="#1a1a24").pack(side="left", padx=4)

        # CONTROL
        cf = ctk.CTkFrame(self.tabs.tab("Control"), fg_color="#0f0f14")
        cf.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(cf, text="CONTROL — full RAT · listener · keylog · android",
                     text_color="#00f0ff", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=6)
        row = ctk.CTkFrame(cf, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="LHOST").pack(side="left")
        self.lhost = ctk.CTkEntry(row, width=130, fg_color="#1a1a24")
        self.lhost.insert(0, "127.0.0.1")
        self.lhost.pack(side="left", padx=4)
        ctk.CTkLabel(row, text="LPORT").pack(side="left")
        self.lport = ctk.CTkEntry(row, width=70, fg_color="#1a1a24")
        self.lport.insert(0, "4444")
        self.lport.pack(side="left", padx=4)
        for txt, k in [("FULL RAT", "rat"), ("LISTENER", "listen"), ("KEYLOGGER", "key"), ("ANDROID RAT", "and")]:
            ctk.CTkButton(row, text=txt, width=110, fg_color="#1a1a24", hover_color="#00f0ff",
                          command=lambda x=k: self.gen_control(x)).pack(side="left", padx=3)
        self.ctrl_status = ctk.CTkLabel(cf, text="shell · file · screenshot · persist · ps · sysinfo", text_color="#00f0ff")
        self.ctrl_status.pack(anchor="w", pady=4)
        self.ctrl_list = ctk.CTkTextbox(cf, height=220, fg_color="#0a0a0c")
        self.ctrl_list.pack(fill="both", expand=True)

        # DESTROY
        df = ctk.CTkFrame(self.tabs.tab("Destroy"), fg_color="#0f0f14")
        df.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(df, text="DESTROY — full combo · wiper · android (more aggressive)",
                     text_color="#ff2a2a", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=6)
        drow = ctk.CTkFrame(df, fg_color="transparent")
        drow.pack(fill="x", pady=4)
        for txt, k in [("FULL DESTROY", "full"), ("WIPER SIM", "wipe"), ("ANDROID DESTROY", "and_d")]:
            ctk.CTkButton(drow, text=txt, width=140, fg_color="#2a0a0a", hover_color="#ff2a2a",
                          command=lambda x=k: self.gen_destroy(x)).pack(side="left", padx=3)
        self.des_status = ctk.CTkLabel(df, text="lock + popups + mem/cpu/disk + ransom-sim + BSOD attempt", text_color="#ff2a2a")
        self.des_status.pack(anchor="w", pady=4)
        self.des_list = ctk.CTkTextbox(df, height=220, fg_color="#0a0a0c")
        self.des_list.pack(fill="both", expand=True)

        # SECURITY
        sf = ctk.CTkFrame(self.tabs.tab("Security"), fg_color="#0f0f14")
        sf.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(sf, text="APP SELF-PROTECTION", text_color="#00f0ff",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=6)
        srow = ctk.CTkFrame(sf, fg_color="transparent")
        srow.pack(fill="x", pady=4)
        ctk.CTkButton(srow, text="CHECK INTEGRITY", command=self.check_integrity, fg_color="#1a1a24").pack(side="left", padx=4)
        ctk.CTkButton(srow, text="RE-SEAL", command=self.reseal, fg_color="#1a1a24").pack(side="left", padx=4)
        ctk.CTkButton(srow, text="ANTI-DEBUG TEST", command=self.test_antidebug, fg_color="#1a1a24").pack(side="left", padx=4)
        self.sec_out = ctk.CTkTextbox(sf, height=300, fg_color="#0a0a0c")
        self.sec_out.pack(fill="both", expand=True, pady=6)

        # TOOLS
        tf = ctk.CTkFrame(self.tabs.tab("Tools"), fg_color="#0f0f14")
        tf.pack(fill="both", expand=True, padx=8, pady=8)
        trow = ctk.CTkFrame(tf, fg_color="transparent")
        trow.pack(fill="x", pady=6)
        ctk.CTkButton(trow, text="Router 192.168.1.1", command=lambda: webbrowser.open("http://192.168.1.1"), fg_color="#1a1a24").pack(side="left", padx=4)
        ctk.CTkButton(trow, text="Local Info", command=self.show_local, fg_color="#1a1a24").pack(side="left", padx=4)
        ctk.CTkButton(trow, text="Figma UI", command=lambda: webbrowser.open("https://www.figma.com/design/4utep1StwcVV22QmJ9pBYe"), fg_color="#1a1a24").pack(side="left", padx=4)
        self.tools_out = ctk.CTkTextbox(tf, height=300, fg_color="#0a0a0c")
        self.tools_out.pack(fill="both", expand=True)

        self.status = ctk.CTkLabel(self.root, text="ready", anchor="w", text_color="#666", fg_color="#0a0a0c")
        self.status.pack(fill="x", padx=12, pady=4)

        self.load_history()
        self.load_bans()
        self.refresh()

    def start_live(self):
        self.scanner.start_live(4.0)
        self.status.configure(text="live scanning active")
        self._live_tick()

    def stop_live(self):
        self.scanner.stop_live()
        self.status.configure(text="live stopped")

    def _live_tick(self):
        if self.scanner.running:
            self.refresh()
            self.root.after(4000, self._live_tick)

    def refresh(self):
        try:
            devices = self.scanner.get_live()
            if not devices:
                found = self.scanner.arp_scan()
                devices = list(found.values())
                with self.scanner.lock:
                    self.scanner.devices.update(found)
            self.live_box.delete("1.0", "end")
            self.live_box.insert("end", f"{'IP':<16} {'MAC':<20} {'MODEL':<22} {'HOSTNAME':<18} {'TYPE':<10} OS\n")
            self.live_box.insert("end", "─"*110 + "\n")
            for d in sorted(devices, key=lambda x: x.ip):
                model = getattr(d, "model", None) or "Unknown Device"
                os_g = getattr(d, "os_guess", "") or "-"
                flag = " [BANNED]" if self.bans.is_banned(d.mac) else ""
                self.live_box.insert("end",
                    f"{d.ip:<16} {d.mac:<20} {str(model)[:20]:<22} {(d.hostname or '-')[:16]:<18} {d.device_type:<10} {os_g}{flag}\n")
            self.status.configure(text=f"devices {len(devices)}  |  local {self.scanner.local_ip}  |  bans {len(self.bans.list_bans())}")
        except Exception as e:
            self.status.configure(text=f"refresh error: {e}")

    def _sel_live(self):
        try:
            idx = self.live_box.index("insert").split(".")[0]
            line = self.live_box.get(f"{idx}.0", f"{idx}.end").strip()
            parts = line.split()
            if len(parts) >= 2 and ":" in parts[1]:
                return parts[0], parts[1]
        except Exception:
            pass
        return None, None

    def _sel_ban(self):
        try:
            idx = self.ban_box.index("insert").split(".")[0]
            line = self.ban_box.get(f"{idx}.0", f"{idx}.end").strip()
            parts = line.split()
            if parts and ":" in parts[0]:
                return parts[0]
        except Exception:
            pass
        return None

    def ban_selected(self):
        ip, mac = self._sel_live()
        if not mac:
            messagebox.showinfo("Ban", "Click a device line first")
            return
        host = ""
        for d in self.scanner.get_live():
            if d.mac == mac:
                host = d.hostname or ""
                break
        self.bans.ban(mac, reason="manual", ip=ip or "", hostname=host)
        self.status.configure(text=f"BANNED {mac} — cannot reconnect while active")
        self.load_bans()
        self.refresh()

    def unban_from_live(self):
        _, mac = self._sel_live()
        if not mac:
            messagebox.showinfo("Unban", "Click a device line first")
            return
        self.bans.unban(mac)
        self.status.configure(text=f"UNBANNED {mac}")
        self.load_bans()
        self.refresh()

    def unban_selected(self):
        mac = self._sel_ban()
        if not mac:
            messagebox.showinfo("Unban", "Click a ban line first")
            return
        self.bans.unban(mac)
        self.status.configure(text=f"UNBANNED {mac}")
        self.load_bans()
        self.refresh()

    def unban_all(self):
        for b in list(self.bans.list_bans()):
            self.bans.unban(b["mac"])
        self.status.configure(text="all unbanned")
        self.load_bans()
        self.refresh()

    def port_scan_selected(self):
        ip, _ = self._sel_live()
        if not ip:
            messagebox.showinfo("Scan", "Select a device")
            return
        self.status.configure(text=f"scanning {ip}")
        def w():
            ports = self.scanner.port_scan(ip)
            self.root.after(0, lambda: messagebox.showinfo("Ports", f"{ip}: {ports or 'none'}"))
        threading.Thread(target=w, daemon=True).start()

    def deauth_selected(self):
        _, mac = self._sel_live()
        if mac:
            ok, msg = self.scanner.deauth(mac)
            messagebox.showinfo("Deauth", msg)

    def copy_mac(self):
        _, mac = self._sel_live()
        if mac:
            self.root.clipboard_clear()
            self.root.clipboard_append(mac)
            self.status.configure(text=f"copied {mac}")

    def load_history(self):
        self.hist_box.delete("1.0", "end")
        for r in self.history.all():
            ts = datetime.fromtimestamp(r.get("last_seen", 0)).strftime("%Y-%m-%d %H:%M")
            model = r.get("model") or "-"
            self.hist_box.insert("end", f"{r.get('mac','')}  {r.get('ip','')}  {str(model)[:18]}  {r.get('hostname','-')[:14]}  x{r.get('seen_count',0)}  {ts}\n")

    def load_bans(self):
        self.ban_box.delete("1.0", "end")
        for b in self.bans.list_bans():
            ts = datetime.fromtimestamp(b.get("banned_at", 0)).strftime("%Y-%m-%d %H:%M")
            self.ban_box.insert("end", f"{b.get('mac')}  {b.get('ip','')}  {b.get('hostname','')}  {ts}  {b.get('reason','')}\n")

    def export_hist(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            self.history.export_csv(Path(path))
            self.status.configure(text=f"exported {path}")

    def export_bans(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.bans.export_json(Path(path))

    def gen_control(self, kind):
        try:
            host = self.lhost.get().strip() or "127.0.0.1"
            port = int(self.lport.get().strip() or "4444")
            if kind == "rat":
                p = self.payloads.control_full_rat(host, port)
            elif kind == "listen":
                p = self.payloads.control_listener(port)
            elif kind == "key":
                p = self.payloads.control_keylogger()
            elif kind == "and":
                p = self.payloads.control_android(host, port)
            else:
                return
            if kind != "listen":
                self.payloads.dropper(p)
            self.ctrl_status.configure(text=f"generated {p.name}")
            self.ctrl_list.delete("1.0", "end")
            for f in sorted(self.payloads.control_dir.glob("*")):
                self.ctrl_list.insert("end", f.name + "\n")
        except Exception as e:
            self.ctrl_status.configure(text=str(e))

    def gen_destroy(self, kind):
        try:
            if kind == "full":
                p = self.payloads.destroy_full()
            elif kind == "wipe":
                p = self.payloads.destroy_wiper_sim()
            elif kind == "and_d":
                p = self.payloads.destroy_android()
            else:
                return
            self.payloads.dropper(p)
            self.des_status.configure(text=f"generated {p.name} + dropper")
            self.des_list.delete("1.0", "end")
            for f in sorted(self.payloads.destroy_dir.glob("*")):
                self.des_list.insert("end", f.name + "\n")
        except Exception as e:
            self.des_status.configure(text=str(e))

    def check_integrity(self):
        if not self.sec: return
        base = Path(__file__).parent
        files = [base / f for f in ("main.py", "scanner.py", "payload.py", "gui.py", "security.py")]
        ok, msg = self.sec.check_integrity(files)
        self.sec_out.insert("end", f"\n[integrity] {msg}\n")

    def reseal(self):
        if not self.sec: return
        base = Path(__file__).parent
        files = [base / f for f in ("main.py", "scanner.py", "payload.py", "gui.py", "security.py")]
        self.sec.seal_integrity(files)
        self.sec_out.insert("end", "\n[integrity] re-sealed\n")

    def test_antidebug(self):
        if not self.sec: return
        clean = self.sec.anti_debug()
        self.sec_out.insert("end", f"\n[anti-debug] {'clean' if clean else 'DEBUGGER DETECTED'}\n")

    def show_local(self):
        self.tools_out.delete("1.0", "end")
        self.tools_out.insert("end", f"Local IP : {self.scanner.local_ip}\n")
        self.tools_out.insert("end", f"Subnet  : {self.scanner.subnet}\n")
        self.tools_out.insert("end", f"Iface   : {self.scanner.iface}\n")
        self.tools_out.insert("end", f"Bans    : {len(self.bans.list_bans())}\n")
        self.tools_out.insert("end", f"History : {len(self.history.all())}\n")

    def run(self):
        self.root.mainloop()
