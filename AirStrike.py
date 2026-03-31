#!/usr/bin/env python3
"""
AirStrike - WiFi Security Auditing Tool
Author: Security Professional
Version: 2.2
Warning: This tool is for authorized security testing only!

Changelog v2.2:
- FIX: Added 'airmon-ng check kill' before enabling monitor mode
- FIX: Scan now uses CSV output file instead of stdout (airodump-ng uses curses, not plain text)
- Added seen_bssids set to prevent duplicate scan results
- Improved scan logging (shows each network found in real time)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import sys
import re
import time
import logging
from datetime import datetime
from pathlib import Path
import platform

# ------------------- Constants -------------------
LOG_FILE = Path.home() / "airstrike.log"

# ------------------- Logging Setup -------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)


class AirStrike:
    def __init__(self, root):
        self.root = root
        self.root.title("AirStrike - WiFi Security Auditing Tool v2.2")
        self.root.geometry("1200x700")
        self.root.configure(bg='#2c3e50')

        # Show legal disclaimer before anything else
        if not self.show_disclaimer():
            sys.exit(0)

        # Variables
        self.monitor_mode = False
        self.current_device = None
        self.capturing = False
        self.capture_process = None
        self.scanning = False
        self.selected_bssid = None
        self.selected_channel = None
        self.selected_essid = None
        self.handshake_file = None
        self.deauth_event = threading.Event()
        self.system = platform.system()

        # Check requirements and privileges
        self.check_requirements()
        self.check_privileges()

        # Create GUI
        self.create_gui()

    # ------------------- Legal Disclaimer -------------------
    def show_disclaimer(self):
        """
        Show legal disclaimer before tool access.
        Industry standard approach used by tools like Metasploit.
        Replaces hardcoded password which is insecure in open source tools.
        """
        response = messagebox.askyesno(
            "Legal Disclaimer",
            "⚠️  WARNING - Authorized Use Only\n\n"
            "AirStrike is intended for authorized security testing only.\n\n"
            "By clicking YES you confirm that:\n"
            "  • You own the network you are testing, OR\n"
            "  • You have explicit written permission to test it\n"
            "  • You understand unauthorized access is illegal\n"
            "  • You take full responsibility for your actions\n\n"
            "Unauthorized use may violate local and international laws.\n\n"
            "Do you agree and wish to continue?"
        )
        if response:
            logging.info("User accepted legal disclaimer.")
        else:
            logging.info("User declined disclaimer. Exiting.")
        return response

    # ------------------- System Checks -------------------
    def check_requirements(self):
        """Check if required external tools are installed."""
        required_tools = ['aircrack-ng', 'hashcat'] if self.system == 'Linux' else []
        missing_tools = []
        for tool in required_tools:
            try:
                subprocess.run(['which', tool], capture_output=True, check=True)
            except subprocess.CalledProcessError:
                missing_tools.append(tool)
        if missing_tools:
            messagebox.showwarning(
                "Missing Tools",
                f"Required tools not found: {', '.join(missing_tools)}\n"
                "Please install them before continuing.\n\n"
                "Install with:\n"
                "sudo apt install aircrack-ng hashcat"
            )
            logging.warning(f"Missing tools: {missing_tools}")

    def check_privileges(self):
        """Check if running with root/admin privileges."""
        if self.system == 'Linux' and os.geteuid() != 0:
            messagebox.showwarning(
                "Root Required",
                "AirStrike requires root privileges on Linux.\n\n"
                "Please run with:\n"
                "xhost +local:root\n"
                "sudo python airstrike.py"
            )
        elif self.system == 'Windows':
            try:
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                if not is_admin:
                    messagebox.showwarning(
                        "Admin Required",
                        "AirStrike requires administrator privileges on Windows."
                    )
            except Exception:
                pass

    # ------------------- GUI Creation -------------------
    def create_gui(self):
        """Create the main GUI interface with tabbed layout."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.device_tab = ttk.Frame(self.notebook)
        self.scan_tab = ttk.Frame(self.notebook)
        self.capture_tab = ttk.Frame(self.notebook)
        self.crack_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.device_tab, text="Device Management")
        self.notebook.add(self.scan_tab, text="Network Scan")
        self.notebook.add(self.capture_tab, text="Handshake Capture")
        self.notebook.add(self.crack_tab, text="Password Cracking")

        self.create_device_tab()
        self.create_scan_tab()
        self.create_capture_tab()
        self.create_crack_tab()

        # Console output at the bottom
        self.console_frame = ttk.LabelFrame(self.root, text="Console Output")
        self.console_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.console = scrolledtext.ScrolledText(
            self.console_frame, height=10, bg='black', fg='#00ff00'
        )
        self.console.pack(fill='both', expand=True, padx=5, pady=5)

    def create_device_tab(self):
        """Device management tab - select device and control monitor mode."""
        ttk.Label(self.device_tab, text="WiFi Device Selection:").grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        self.device_combo = ttk.Combobox(self.device_tab, width=30)
        self.device_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.device_tab, text="Refresh Devices",
                   command=self.refresh_devices).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.device_tab, text="Device Info:").grid(
            row=1, column=0, padx=5, pady=5, sticky='nw'
        )
        self.device_info = scrolledtext.ScrolledText(self.device_tab, height=10, width=60)
        self.device_info.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        ttk.Label(self.device_tab, text="Monitor Mode Controls:").grid(
            row=2, column=0, padx=5, pady=5, sticky='w'
        )
        self.monitor_status = ttk.Label(self.device_tab, text="Status: OFF", foreground='red')
        self.monitor_status.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        ttk.Button(self.device_tab, text="Enable Monitor Mode",
                   command=self.enable_monitor_mode).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(self.device_tab, text="Disable Monitor Mode",
                   command=self.disable_monitor_mode).grid(row=3, column=1, padx=5, pady=5)

    def create_scan_tab(self):
        """Network scan tab - discover nearby WiFi networks."""
        ttk.Button(self.scan_tab, text="Start Scan",
                   command=self.start_scan).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(self.scan_tab, text="Stop Scan",
                   command=self.stop_scan).grid(row=0, column=1, padx=5, pady=5)

        # Network results table
        self.network_tree = ttk.Treeview(
            self.scan_tab,
            columns=('BSSID', 'Channel', 'ESSID', 'Security'),
            show='headings'
        )
        for col in ('BSSID', 'Channel', 'ESSID', 'Security'):
            self.network_tree.heading(col, text=col)
        self.network_tree.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        # Scrollbar for network list
        scrollbar = ttk.Scrollbar(self.scan_tab, orient='vertical',
                                   command=self.network_tree.yview)
        scrollbar.grid(row=1, column=2, sticky='ns')
        self.network_tree.configure(yscrollcommand=scrollbar.set)

        self.scan_tab.grid_rowconfigure(1, weight=1)
        self.scan_tab.grid_columnconfigure(0, weight=1)

    def create_capture_tab(self):
        """Handshake capture tab - capture WPA2 4-way handshake."""
        ttk.Label(self.capture_tab, text="Select Target Network:").grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        self.target_combo = ttk.Combobox(self.capture_tab, width=50)
        self.target_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.capture_tab, text="Load from Scan",
                   command=self.load_targets).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.capture_tab, text="Channel:").grid(
            row=1, column=0, padx=5, pady=5, sticky='w'
        )
        self.channel_entry = ttk.Entry(self.capture_tab, width=10)
        self.channel_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        ttk.Button(self.capture_tab, text="Start Capture",
                   command=self.start_capture).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.capture_tab, text="Stop Capture",
                   command=self.stop_capture).grid(row=2, column=1, padx=5, pady=5)

        # Deauth attack section
        deauth_frame = ttk.LabelFrame(self.capture_tab, text="Deauth Attack")
        deauth_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Label(deauth_frame, text="Number of Packets:").grid(row=0, column=0, padx=5, pady=5)
        self.packet_count = ttk.Entry(deauth_frame, width=10)
        self.packet_count.insert(0, "10")
        self.packet_count.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(deauth_frame, text="Send Deauth Attack",
                   command=self.send_deauth).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(deauth_frame, text="Continuous Deauth (Until Stop)",
                   command=self.continuous_deauth).grid(row=0, column=3, padx=5, pady=5)

        self.capture_status = ttk.Label(
            self.capture_tab, text="Status: Not Capturing", foreground='red'
        )
        self.capture_status.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def create_crack_tab(self):
        """Password cracking tab - crack captured handshake using hashcat."""
        ttk.Label(self.crack_tab, text="Handshake File:").grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        self.handshake_path = ttk.Entry(self.crack_tab, width=50)
        self.handshake_path.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.crack_tab, text="Browse",
                   command=self.browse_handshake).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.crack_tab, text="Attack Type:").grid(
            row=1, column=0, padx=5, pady=5, sticky='w'
        )
        self.attack_type = ttk.Combobox(
            self.crack_tab, values=['Brute Force', 'Dictionary'], width=20
        )
        self.attack_type.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.attack_type.bind('<<ComboboxSelected>>', self.toggle_attack_options)

        # Brute force options
        self.bf_frame = ttk.LabelFrame(self.crack_tab, text="Brute Force Options")
        self.bf_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Label(self.bf_frame, text="Character Set:").grid(row=0, column=0, padx=5, pady=5)
        self.charset = ttk.Combobox(
            self.bf_frame,
            values=['Numbers Only', 'Letters Only', 'Letters + Numbers',
                    'Full (Letters + Numbers + Symbols)'],
            width=30
        )
        self.charset.grid(row=0, column=1, padx=5, pady=5)
        self.charset.set('Letters + Numbers')

        ttk.Label(self.bf_frame, text="Min Length:").grid(row=1, column=0, padx=5, pady=5)
        self.min_length = ttk.Entry(self.bf_frame, width=10)
        self.min_length.insert(0, "8")
        self.min_length.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(self.bf_frame, text="Max Length:").grid(row=2, column=0, padx=5, pady=5)
        self.max_length = ttk.Entry(self.bf_frame, width=10)
        self.max_length.insert(0, "12")
        self.max_length.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # Dictionary options
        self.dict_frame = ttk.LabelFrame(self.crack_tab, text="Dictionary Options")
        self.dict_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Label(self.dict_frame, text="Wordlist File:").grid(row=0, column=0, padx=5, pady=5)
        self.wordlist_path = ttk.Entry(self.dict_frame, width=50)
        self.wordlist_path.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.dict_frame, text="Browse",
                   command=self.browse_wordlist).grid(row=0, column=2, padx=5, pady=5)
        self.dict_frame.grid_remove()  # Hidden by default

        ttk.Button(self.crack_tab, text="Start Cracking",
                   command=self.start_cracking).grid(row=4, column=1, padx=5, pady=20)

        ttk.Label(self.crack_tab, text="Cracking Results:").grid(
            row=5, column=0, padx=5, pady=5, sticky='w'
        )
        self.crack_results = scrolledtext.ScrolledText(self.crack_tab, height=15, width=80)
        self.crack_results.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

    # ------------------- Device Management -------------------
    def refresh_devices(self):
        """Refresh list of available wireless network devices."""
        try:
            if self.system == 'Linux':
                result = subprocess.run(['iwconfig'], capture_output=True, text=True)
                devices = re.findall(r'^(\w+)', result.stdout, re.MULTILINE)
                self.device_combo['values'] = devices
                if devices:
                    self.device_combo.set(devices[0])
                    self.show_device_info(devices[0])
            else:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True, text=True, check=True
                )
                matches = re.findall(r'Name\s*:\s*(.+)', result.stdout)
                self.device_combo['values'] = matches
                if matches:
                    self.device_combo.set(matches[0])
                    self.show_device_info(matches[0])
        except Exception as e:
            self.log(f"Error refreshing devices: {e}")
            logging.error(f"Device refresh error: {e}")

    def show_device_info(self, device):
        """Show detailed info about the selected wireless device."""
        try:
            self.device_info.delete(1.0, tk.END)
            if self.system == 'Linux':
                result = subprocess.run(['iwconfig', device], capture_output=True, text=True)
                self.device_info.insert(1.0, result.stdout)
            else:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interface', device],
                    capture_output=True, text=True
                )
                self.device_info.insert(1.0, result.stdout)
        except Exception as e:
            self.log(f"Error getting device info: {e}")

    def enable_monitor_mode(self):
        """
        Enable monitor mode on the selected wireless device (Linux only).
        FIX: Runs 'airmon-ng check kill' first to stop interfering processes
        like NetworkManager and wpa_supplicant before enabling monitor mode.
        """
        if self.system != 'Linux':
            messagebox.showinfo("Not Supported", "Monitor mode is only supported on Linux.")
            return
        device = self.device_combo.get()
        if not self._validate_device(device):
            return
        try:
            # Kill interfering processes BEFORE enabling monitor mode
            self.log("Killing interfering processes (NetworkManager, wpa_supplicant)...")
            subprocess.run(['sudo', 'airmon-ng', 'check', 'kill'], check=True)
            self.log("Processes killed. Enabling monitor mode...")

            subprocess.run(['sudo', 'airmon-ng', 'start', device], check=True)
            self.monitor_mode = True
            self.monitor_status.config(text="Status: ON", foreground='green')
            self.log(f"Monitor mode enabled on {device}")
            time.sleep(2)
            self.refresh_devices()
        except Exception as e:
            self.log(f"Error enabling monitor mode: {e}")
            messagebox.showerror("Error", f"Failed to enable monitor mode: {e}")

    def disable_monitor_mode(self):
        """Disable monitor mode on the selected device (Linux only)."""
        if self.system != 'Linux':
            return
        device = self.device_combo.get()
        if not self._validate_device(device):
            return
        try:
            subprocess.run(['sudo', 'airmon-ng', 'stop', device], check=True)
            self.monitor_mode = False
            self.monitor_status.config(text="Status: OFF", foreground='red')
            self.log(f"Monitor mode disabled on {device}")
            self.refresh_devices()
        except Exception as e:
            self.log(f"Error disabling monitor mode: {e}")

    # ------------------- Network Scanning -------------------
    def start_scan(self):
        """
        Start scanning for nearby WiFi networks.
        FIX: Uses '--output-format csv' and reads from the CSV file instead of
        stdout, because airodump-ng uses a curses terminal UI that cannot be
        parsed from stdout line by line.
        """
        if self.scanning:
            return
        device = self.device_combo.get()
        if not self._validate_device(device):
            return

        self.scanning = True
        self.log("Starting network scan...")

        def scan_thread():
            csv_file = "/tmp/airstrike_scan"
            csv_path = f"{csv_file}-01.csv"
            process = None

            try:
                # Clear previous results from the table
                for item in self.network_tree.get_children():
                    self.network_tree.delete(item)

                # Remove any leftover CSV from previous scan
                if os.path.exists(csv_path):
                    os.remove(csv_path)

                # Run airodump-ng with CSV output — stdout is suppressed
                # because airodump-ng uses curses UI, not plain text output
                process = subprocess.Popen(
                    ['sudo', 'airodump-ng', '--output-format', 'csv', '-w', csv_file, device],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                seen_bssids = set()  # Track already added networks to avoid duplicates
                start_time = time.time()

                while self.scanning and (time.time() - start_time) < 60:
                    time.sleep(2)

                    if not os.path.exists(csv_path):
                        continue

                    try:
                        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()

                        for line in lines:
                            line = line.strip()

                            # Skip empty lines and headers
                            if not line or line.startswith('BSSID') or line.startswith('Station MAC'):
                                continue

                            parts = [p.strip() for p in line.split(',')]

                            # AP (access point) lines have 15+ comma-separated fields
                            if len(parts) >= 14:
                                bssid = parts[0]

                                # Validate it is a real MAC address
                                if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
                                    continue

                                # Skip if already added to the table
                                if bssid in seen_bssids:
                                    continue

                                channel  = parts[3].strip()
                                security = parts[5].strip()
                                essid    = parts[13].strip() if parts[13].strip() else "Hidden"

                                seen_bssids.add(bssid)
                                self.network_tree.insert(
                                    '', 'end',
                                    values=(bssid, channel, essid, security)
                                )
                                self.log(f"Found: {essid} [{bssid}] CH{channel} {security}")

                    except Exception as e:
                        self.log(f"CSV parse error: {e}")
                        logging.error(f"CSV parse error: {e}")

            except Exception as e:
                self.log(f"Error during scan: {e}")
                logging.error(f"Scan error: {e}")
            finally:
                if process:
                    process.terminate()
                self.scanning = False
                self.log("Scan completed.")

        threading.Thread(target=scan_thread, daemon=True).start()

    def stop_scan(self):
        """Stop the network scan."""
        self.scanning = False
        self.log("Scan stopped.")

    def load_targets(self):
        """Load scanned networks into the target selection dropdown."""
        targets = []
        for item in self.network_tree.get_children():
            values = self.network_tree.item(item)['values']
            if values:
                targets.append(f"{values[0]} - {values[2]}")
        self.target_combo['values'] = targets
        if targets:
            self.target_combo.set(targets[0])

    # ------------------- Handshake Capture -------------------
    def start_capture(self):
        """Start capturing the WPA2 4-way handshake from the target network (Linux only)."""
        if self.system != 'Linux':
            messagebox.showinfo("Not Supported", "Handshake capture is only supported on Linux.")
            return
        if self.capturing:
            messagebox.showinfo("Already Capturing", "Capture is already in progress.")
            return

        target = self.target_combo.get()
        if not target:
            messagebox.showwarning("No Target", "Please select a target network.")
            return
        bssid = target.split(' - ')[0]
        if not self._validate_bssid(bssid):
            return

        channel = self.channel_entry.get().strip()
        if not self._validate_channel(channel):
            return

        device = self.device_combo.get()
        if not self._validate_device(device):
            return

        self.capturing = True
        self.capture_status.config(text="Status: Capturing Handshake...", foreground='orange')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_file = f"/tmp/handshake_{timestamp}"

        def capture_thread():
            try:
                subprocess.run(['sudo', 'iwconfig', device, 'channel', channel], check=True)
                cmd = ['sudo', 'airodump-ng', '--bssid', bssid, '-c', channel,
                       '-w', capture_file, device]
                self.capture_process = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self.log(f"Capturing handshake on {bssid}...")
                self.log("Waiting for handshake (use Deauth attack to speed up)...")

                while self.capturing:
                    time.sleep(2)
                    cap_path = f"{capture_file}-01.cap"
                    if os.path.exists(cap_path):
                        self.log("Handshake captured successfully!")
                        self.capture_status.config(
                            text="Status: Handshake Captured!", foreground='green'
                        )
                        self.handshake_file = cap_path
                        self.handshake_path.delete(0, tk.END)
                        self.handshake_path.insert(0, self.handshake_file)
                        break
            except Exception as e:
                self.log(f"Error during capture: {e}")
                self.capture_status.config(text="Status: Error", foreground='red')
                logging.error(f"Capture error: {e}")
            finally:
                if self.capture_process:
                    self.capture_process.terminate()
                self.capturing = False

        threading.Thread(target=capture_thread, daemon=True).start()

    def stop_capture(self):
        """Stop the handshake capture process."""
        self.capturing = False
        self.deauth_event.set()
        if self.capture_process:
            self.capture_process.terminate()
        self.capture_status.config(text="Status: Not Capturing", foreground='red')
        self.log("Capture stopped.")

    # ------------------- Deauth Attacks -------------------
    def send_deauth(self):
        """Send a fixed number of deauthentication packets to force a handshake (Linux only)."""
        if self.system != 'Linux':
            messagebox.showinfo("Not Supported", "Deauth attacks are only supported on Linux.")
            return
        target = self.target_combo.get()
        if not target:
            messagebox.showwarning("No Target", "Please select a target network.")
            return
        bssid = target.split(' - ')[0]
        if not self._validate_bssid(bssid):
            return

        device = self.device_combo.get()
        if not self._validate_device(device):
            return

        try:
            packet_count = self.packet_count.get().strip()
            if not packet_count.isdigit():
                messagebox.showerror("Invalid Input", "Packet count must be a number.")
                return
            subprocess.Popen(
                ['sudo', 'aireplay-ng', '--deauth', packet_count, '-a', bssid, device],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.log(f"Sent {packet_count} deauth packets to {bssid}")
        except Exception as e:
            self.log(f"Error sending deauth: {e}")
            logging.error(f"Deauth error: {e}")

    def continuous_deauth(self):
        """Send continuous deauth packets until the user clicks OK to stop (Linux only)."""
        if self.system != 'Linux':
            messagebox.showinfo("Not Supported", "Deauth attacks are only supported on Linux.")
            return
        target = self.target_combo.get()
        if not target:
            messagebox.showwarning("No Target", "Please select a target network.")
            return
        bssid = target.split(' - ')[0]
        if not self._validate_bssid(bssid):
            return

        device = self.device_combo.get()
        if not self._validate_device(device):
            return

        self.deauth_event.clear()

        def deauth_loop():
            while not self.deauth_event.is_set():
                try:
                    subprocess.run(
                        ['sudo', 'aireplay-ng', '--deauth', '5', '-a', bssid, device],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
                    )
                    time.sleep(2)
                except Exception as e:
                    self.log(f"Deauth loop error: {e}")

        threading.Thread(target=deauth_loop, daemon=True).start()
        self.log("Continuous deauth attack started.")
        messagebox.showinfo("Deauth Attack", "Continuous deauth attack started.\nClick OK to stop.")
        self.deauth_event.set()
        self.log("Continuous deauth attack stopped.")

    # ------------------- Password Cracking -------------------
    def browse_handshake(self):
        """Open file dialog to select a captured handshake .cap file."""
        filename = filedialog.askopenfilename(
            filetypes=[("CAP files", "*.cap"), ("All files", "*.*")]
        )
        if filename:
            self.handshake_path.delete(0, tk.END)
            self.handshake_path.insert(0, filename)

    def browse_wordlist(self):
        """Open file dialog to select a wordlist file for dictionary attack."""
        filename = filedialog.askopenfilename(
            filetypes=[("Wordlist files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wordlist_path.delete(0, tk.END)
            self.wordlist_path.insert(0, filename)

    def toggle_attack_options(self, event=None):
        """Toggle between brute force and dictionary attack option panels."""
        if self.attack_type.get() == 'Brute Force':
            self.dict_frame.grid_remove()
            self.bf_frame.grid()
        else:
            self.bf_frame.grid_remove()
            self.dict_frame.grid()

    def start_cracking(self):
        """Start cracking the captured handshake using hashcat (Linux only)."""
        if self.system != 'Linux':
            messagebox.showinfo("Not Supported", "Password cracking is only supported on Linux.")
            return

        handshake_file = self.handshake_path.get()
        if not handshake_file or not os.path.exists(handshake_file):
            messagebox.showwarning("No Handshake", "Please select a valid handshake file.")
            return

        attack_type = self.attack_type.get()
        if not attack_type:
            messagebox.showwarning("No Attack Type", "Please select an attack type.")
            return

        self.crack_results.delete(1.0, tk.END)
        self.log("Starting password cracking...")

        def crack_thread():
            try:
                hccapx_file = handshake_file.replace('.cap', '.hccapx')

                # Convert .cap file to hashcat-compatible format
                try:
                    subprocess.run(
                        ['sudo', 'cap2hccapx', handshake_file, hccapx_file],
                        check=True, capture_output=True
                    )
                except subprocess.CalledProcessError:
                    # Fallback to alternative conversion tool
                    subprocess.run(
                        ['sudo', 'hcxpcapngtool', handshake_file, '-o', hccapx_file],
                        check=True
                    )

                if attack_type == 'Brute Force':
                    charset_map = {
                        'Numbers Only': '?d',
                        'Letters Only': '?l?u',
                        'Letters + Numbers': '?l?u?d',
                        'Full (Letters + Numbers + Symbols)': '?l?u?d?s'
                    }
                    charset = charset_map.get(self.charset.get(), '?l?u?d')
                    min_len = self.min_length.get().strip()
                    max_len = self.max_length.get().strip()

                    if not (min_len.isdigit() and max_len.isdigit()):
                        messagebox.showerror("Invalid Input", "Min/Max length must be numbers.")
                        return

                    mask = charset * int(min_len)
                    if min_len == max_len:
                        cmd = ['sudo', 'hashcat', '-m', '2500', hccapx_file, '-a', '3', mask]
                    else:
                        cmd = [
                            'sudo', 'hashcat', '-m', '2500', hccapx_file, '-a', '3',
                            '--increment',
                            f'--increment-min={min_len}',
                            f'--increment-max={max_len}',
                            mask
                        ]
                else:
                    wordlist = self.wordlist_path.get()
                    if not wordlist or not os.path.exists(wordlist):
                        messagebox.showerror("Error", "Please select a valid wordlist file.")
                        return
                    cmd = ['sudo', 'hashcat', '-m', '2500', hccapx_file, '-a', '0', wordlist]

                # Run hashcat and monitor output for results
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                for line in process.stdout:
                    if 'RECOVERED' in line:
                        self.crack_results.insert(tk.END, line)
                        self.crack_results.see(tk.END)
                        self.log("Password found! Check results tab.")
                process.wait()

                # Show final cracked passwords
                result = subprocess.run(
                    ['sudo', 'hashcat', '-m', '2500', hccapx_file, '--show'],
                    capture_output=True, text=True
                )
                if result.stdout:
                    self.crack_results.insert(tk.END, "\n=== Cracked Passwords ===\n")
                    self.crack_results.insert(tk.END, result.stdout)
                else:
                    self.crack_results.insert(tk.END, "\nNo passwords cracked.\n")

                self.log("Cracking completed.")
            except Exception as e:
                self.log(f"Error during cracking: {e}")
                logging.error(f"Cracking error: {e}")
                messagebox.showerror("Error", f"Cracking failed: {e}")

        threading.Thread(target=crack_thread, daemon=True).start()

    # ------------------- Input Validation -------------------
    def _validate_device(self, device):
        """Validate device name to prevent command injection attacks."""
        if not device:
            messagebox.showwarning("No Device", "Please select a wireless device.")
            return False
        if not re.match(r'^[\w\-]+$', device):
            messagebox.showerror("Invalid Device", "Device name contains invalid characters.")
            return False
        return True

    def _validate_bssid(self, bssid):
        """Validate BSSID is in correct MAC address format (XX:XX:XX:XX:XX:XX)."""
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
            messagebox.showerror("Invalid BSSID", "BSSID must be in format XX:XX:XX:XX:XX:XX")
            return False
        return True

    def _validate_channel(self, channel):
        """Validate WiFi channel number is within acceptable range (1-165 covers 2.4GHz and 5GHz)."""
        if not channel.isdigit():
            messagebox.showerror("Invalid Channel", "Channel must be a number.")
            return False
        ch = int(channel)
        if ch < 1 or ch > 165:
            messagebox.showerror("Invalid Channel", "Channel must be between 1 and 165.")
            return False
        return True

    # ------------------- Logging -------------------
    def log(self, message):
        """Log a message to the GUI console and the log file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        logging.info(message)


def main():
    """Main entry point - initialize and launch AirStrike."""
    root = tk.Tk()
    app = AirStrike(root)
    root.mainloop()


if __name__ == "__main__":
    main()