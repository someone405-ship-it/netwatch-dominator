#!/usr/bin/env python3
"""CustomTkinter GUI for NetWatch Dominator"""

import customtkinter as ctk
import threading
import time
from datetime import datetime
from tkinter import messagebox, filedialog
import webbrowser

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class DominatorGUI:
    def __init__(self, scanner, bans, history, payloads):
        self.scanner = scanner
        self.bans = bans
        self.history = history
        self.payloads = payloads
        self.root = ctk.CTk()
        self.root.title("NetWatch Dominator")
        self.root.geometry("1100x700")
        self.selected_mac = None
        self._build()

    def _build(self):
        # top bar
        top = ctk.CTkFrame(self.root)
        top.pack(fill="x", padx=8, pady=6)
        ctk.CTkLabel(top, text="NetWatch Dominator", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Refresh Now", width=100, command=self.refresh).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Start Live", width=100, command=self.start_live).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Stop Live", width=100, command=self.stop_live).pack(side="right", padx=4)
        self.theme_btn = ctk.CTkButton(top, text="Light", width=70, command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=4)

        # tabs
        self.tabs = ctk.CTkTabview(self.root)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=4)
        self.tab_live = self.tabs.add("Live")
        self.tab_hist = self.tabs.add("History")
        self.tab_ban = self.tabs.add("Bans")
        self.tab_pay = self.tabs.add("Payloads")
        self.tab_tools = self.tabs.add("Tools")

        # Live tab
        self.live_box = ctk.CTkTextbox(self.tab_live, font=ctk.CTkFont(family="Consolas", size=13))
        self.live_box.pack(fill="both", expand=True, padx=4, pady=4)
        live_btn = ctk.CTkFrame(self.tab_live)
        live_btn.pack(fill="x", pady=4)
        ctk.CTkButton(live_btn, text="Ban Selected", command=self.ban_selected).pack(side="left", padx=4)
        ctk.CTkButton(live_btn, text="Port Scan", command=self.port_scan_selected).pack(side="left", padx=4)
        ctk.CTkButton(live_btn, text="Deauth (lab)", command=self.deauth_selected).pack(side="left", padx=4)
        ctk.CTkButton(live_btn, text="Copy MAC", command=self.copy_mac).pack(side="left", padx=4)

        # History
        self.hist_box = ctk.CTkTextbox(self.tab_hist, font=ctk.CTkFont(family="Consolas", size=12))
        self.hist_box.pack(fill="both", expand=True, padx=4, pady=4)
        hist_btn = ctk.CTkFrame(self.tab_hist)
        hist_btn.pack(fill="x")
        ctk.CTkButton(hist_btn, text="Reload History", command=self.load_history).pack(side="left", padx=4)
        ctk.CTkButton(hist_btn, text="Export CSV", command=self.export_hist).pack(side="left", padx=4)

        # Bans
        self.ban_box = ctk.CTkTextbox(self.tab_ban, font=ctk.CTkFont(family="Consolas", size=12))
        self.ban_box.pack(fill="both", expand=True, padx=4, pady=4)
        ban_btn = ctk.CTkFrame(self.tab_ban)
        ban_btn.pack(fill="x")
        ctk.CTkButton(ban_btn, text="Refresh Bans", command=self.load_bans).pack(side="left", padx=4)
        ctk.CTkButton(ban_btn, text="Unban Selected", command=self.unban_selected).pack(side="left", padx=4)
        ctk.CTkButton(ban_btn, text="Export Bans", command=self.export_bans).pack(side="left", padx=4)

        # Payloads
        pay_f = ctk.CTkFrame(self.tab_pay)
        pay_f.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(pay_f, text="Generate payloads (saved to ./payloads)", font=ctk.CTkFont(size=14)).pack(anchor="w")
        row1 = ctk.CTkFrame(pay_f)
        row1.pack(fill="x", pady=6)
        ctk.CTkButton(row1, text="Crash Loop", command=lambda: self.gen("crash")).pack(side="left", padx=4)
        ctk.CTkButton(row1, text="Popup Spam", command=lambda: self.gen("popup")).pack(side="left", padx=4)
        ctk.CTkButton(row1, text="Screen Flash", command=lambda: self.gen("screen")).pack(side="left", padx=4)
        ctk.CTkButton(row1, text="Keylogger", command=lambda: self.gen("keylog")).pack(side="left", padx=4)
        row2 = ctk.CTkFrame(pay_f)
        row2.pack(fill="x", pady=6)
        ctk.CTkLabel(row2, text="RevShell Host:").pack(side="left")
        self.rs_host = ctk.CTkEntry(row2, width=140)
        self.rs_host.insert(0, "127.0.0.1")
        self.rs_host.pack(side="left", padx=4)
        ctk.CTkLabel(row2, text="Port:").pack(side="left")
        self.rs_port = ctk.CTkEntry(row2, width=70)
        self.rs_port.insert(0, "4444")
        self.rs_port.pack(side="left", padx=4)
        ctk.CTkButton(row2, text="Gen Reverse Shell", command=lambda: self.gen("rev")).pack(side="left", padx=8)
        ctk.CTkButton(row2, text="Gen Dropper .bat", command=lambda: self.gen("bat")).pack(side="left", padx=4)
        self.pay_status = ctk.CTkLabel(pay_f, text="")
        self.pay_status.pack(anchor="w", pady=8)
        self.pay_list = ctk.CTkTextbox(pay_f, height=180)
        self.pay_list.pack(fill="both", expand=True)

        # Tools
        tools = ctk.CTkFrame(self.tab_tools)
        tools.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(tools, text="Extra tools", font=ctk.CTkFont(size=14)).pack(anchor="w")
        trow = ctk.CTkFrame(tools)
        trow.pack(fill="x", pady=6)
        ctk.CTkButton(trow, text="Open Router Admin (192.168.1.1)", command=lambda: webbrowser.open("http://192.168.1.1")).pack(side="left", padx=4)
        ctk.CTkButton(trow, text="Open 192.168.0.1", command=lambda: webbrowser.open("http://192.168.0.1")).pack(side="left", padx=4)
        ctk.CTkButton(trow, text="Show Local IP", command=self.show_local).pack(side="left", padx=4)
        self.tools_out = ctk.CTkTextbox(tools, height=200)
        self.tools_out.pack(fill="both", expand=True, pady=6)

        # status
        self.status = ctk.CTkLabel(self.root, text="Ready", anchor="w")
        self.status.pack(fill="x", padx=10, pady=4)

        self.load_history()
        self.load_bans()
        self.refresh()

    def toggle_theme(self):
        cur = ctk.get_appearance_mode()
        new = "Light" if cur == "Dark" else "Dark"
        ctk.set_appearance_mode(new)
        self.theme_btn.configure(text="Dark" if new == "Light" else "Light")

    def start_live(self):
        self.scanner.start_live(4.0)
        self.status.configure(text="Live scanning...")
        self._live_tick()

    def stop_live(self):
        self.scanner.stop_live()
        self.status.configure(text="Live stopped")

    def _live_tick(self):
        if self.scanner.running:
            self.refresh()
            self.root.after(4000, self._live_tick)

    def refresh(self):
        devices = self.scanner.get_live()
        if not devices:
            # one-shot scan
            found = self.scanner.arp_scan()
            devices = list(found.values())
            with self.scanner.lock:
                self.scanner.devices.update(found)
        self.live_box.delete("1.0", "end")
        header = f"{'IP':<16} {'MAC':<20} {'Hostname':<22} {'Vendor':<14} {'Type':<10} Online\n"
        self.live_box.insert("end", header)
        self.live_box.insert("end", "-"*100 + "\n")
        for d in sorted(devices, key=lambda x: x.ip):
            line = f"{d.ip:<16} {d.mac:<20} {(d.hostname or '-')[:20]:<22} {(d.vendor or '-')[:12]:<14} {d.device_type:<10} {'YES' if d.is_online else 'no'}\n"
            self.live_box.insert("end", line)
        self.status.configure(text=f"Devices: {len(devices)} | Local: {self.scanner.local_ip}")

    def _selected_line(self):
        try:
            idx = self.live_box.index("insert").split(".")[0]
            line = self.live_box.get(f"{idx}.0", f"{idx}.end")
            parts = line.split()
            if len(parts) >= 2 and ":" in parts[1]:
                return parts[0], parts[1]
        except Exception:
            pass
        return None, None

    def ban_selected(self):
        ip, mac = self._selected_line()
        if not mac:
            messagebox.showinfo("Ban", "Click a device line first")
            return
        self.bans.ban(mac, reason="manual", ip=ip or "")
        self.status.configure(text=f"Banned {mac}")
        self.load_bans()
        self.refresh()

    def unban_selected(self):
        try:
            idx = self.ban_box.index("insert").split(".")[0]
            line = self.ban_box.get(f"{idx}.0", f"{idx}.end")
            parts = line.split()
            if parts and ":" in parts[0]:
                mac = parts[0]
                self.bans.unban(mac)
                self.status.configure(text=f"Unbanned {mac}")
                self.load_bans()
        except Exception:
            messagebox.showinfo("Unban", "Click a ban line first")

    def port_scan_selected(self):
        ip, mac = self._selected_line()
        if not ip:
            messagebox.showinfo("Scan", "Select a device")
            return
        self.status.configure(text=f"Port scanning {ip}...")
        def work():
            ports = self.scanner.port_scan(ip)
            self.root.after(0, lambda: self._show_ports(ip, ports))
        threading.Thread(target=work, daemon=True).start()

    def _show_ports(self, ip, ports):
        messagebox.showinfo("Ports", f"{ip} open: {ports or 'none'}")
        self.status.configure(text=f"Port scan done for {ip}")

    def deauth_selected(self):
        ip, mac = self._selected_line()
        if not mac:
            return
        ok, msg = self.scanner.deauth(mac)
        messagebox.showinfo("Deauth", msg)

    def copy_mac(self):
        ip, mac = self._selected_line()
        if mac:
            self.root.clipboard_clear()
            self.root.clipboard_append(mac)
            self.status.configure(text=f"Copied {mac}")

    def load_history(self):
        self.hist_box.delete("1.0", "end")
        for r in self.history.all():
            ts = datetime.fromtimestamp(r.get("last_seen", 0)).strftime("%Y-%m-%d %H:%M")
            line = f"{r.get('mac','')}  {r.get('ip','')}  {r.get('hostname','-')[:18]}  seen={r.get('seen_count',0)}  last={ts}\n"
            self.hist_box.insert("end", line)

    def load_bans(self):
        self.ban_box.delete("1.0", "end")
        for b in self.bans.list_bans():
            ts = datetime.fromtimestamp(b.get("banned_at", 0)).strftime("%Y-%m-%d %H:%M")
            line = f"{b.get('mac')}  {b.get('ip','')}  {b.get('hostname','')}  banned={ts}  {b.get('reason','')}\n"
            self.ban_box.insert("end", line)

    def export_hist(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            self.history.export_csv(Path(path))
            self.status.configure(text=f"Exported history -> {path}")

    def export_bans(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            self.bans.export_json(Path(path))
            self.status.configure(text=f"Exported bans -> {path}")

    def gen(self, kind):
        try:
            if kind == "crash":
                p = self.payloads.crash_loop()
            elif kind == "popup":
                p = self.payloads.random_popups()
            elif kind == "screen":
                p = self.payloads.screen_spam()
            elif kind == "keylog":
                p = self.payloads.keylogger()
            elif kind == "rev":
                host = self.rs_host.get().strip() or "127.0.0.1"
                port = int(self.rs_port.get().strip() or "4444")
                p = self.payloads.reverse_shell(host, port)
            elif kind == "bat":
                # last py in payloads
                pys = list(self.payloads.out_dir.glob("*.py"))
                if not pys:
                    self.pay_status.configure(text="Generate a .py first")
                    return
                p = self.payloads.dropper_bat(str(pys[-1].name))
            else:
                return
            self.pay_status.configure(text=f"Generated: {p}")
            self.pay_list.delete("1.0", "end")
            for f in self.payloads.list_generated():
                self.pay_list.insert("end", str(f.name) + "\n")
        except Exception as e:
            self.pay_status.configure(text=str(e))

    def show_local(self):
        self.tools_out.delete("1.0", "end")
        self.tools_out.insert("end", f"Local IP: {self.scanner.local_ip}\n")
        self.tools_out.insert("end", f"Subnet:  {self.scanner.subnet}\n")
        self.tools_out.insert("end", f"Iface:   {self.scanner.iface}\n")

    def run(self):
        self.root.mainloop()

from pathlib import Path
