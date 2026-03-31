"""
ui/capture_tab.py
Handshake Capture tab UI.
Controls handshake capture and deauth attacks.
Talks to core/capture.py and core/deauth.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from core.capture import HandshakeCapture
from core.deauth import DeauthAttack


class CaptureTab:
    """Builds and manages the Handshake Capture tab."""

    def __init__(self, notebook, get_device_callback, log_callback):
        """
        Args:
            notebook:            The ttk.Notebook to attach this tab to
            get_device_callback: Function that returns the selected device name
            log_callback:        Function to write messages to the console
        """
        self.log        = log_callback
        self.get_device = get_device_callback
        self.capture    = HandshakeCapture()
        self.deauth     = DeauthAttack()

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Handshake Capture")
        self._build_ui()

    def _build_ui(self):
        """Build all widgets for the Handshake Capture tab."""
        # Target network selection
        ttk.Label(self.frame, text="Target Network:").grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        self.target_combo = ttk.Combobox(self.frame, width=50)
        self.target_combo.grid(row=0, column=1, padx=5, pady=5)
        self.target_combo.bind('<<ComboboxSelected>>', self._on_target_selected)
        ttk.Button(self.frame, text="Load from Scan",
                   command=self._load_targets_prompt).grid(row=0, column=2, padx=5, pady=5)

        # Channel entry
        ttk.Label(self.frame, text="Channel:").grid(
            row=1, column=0, padx=5, pady=5, sticky='w'
        )
        self.channel_entry = ttk.Entry(self.frame, width=10)
        self.channel_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        # Capture controls
        ttk.Button(self.frame, text="Start Capture",
                   command=self.start_capture).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Stop Capture",
                   command=self.stop_capture).grid(row=2, column=1, padx=5, pady=5)

        self.auto_assist_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.frame,
            text="Auto-assist capture (send timed deauth bursts)",
            variable=self.auto_assist_var
        ).grid(row=2, column=2, padx=5, pady=5, sticky='w')

        # Deauth attack section
        deauth_frame = ttk.LabelFrame(self.frame, text="Deauth Attack")
        deauth_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Label(deauth_frame, text="Packets:").grid(row=0, column=0, padx=5, pady=5)
        self.packet_count = ttk.Entry(deauth_frame, width=10)
        self.packet_count.insert(0, "10")
        self.packet_count.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(deauth_frame, text="Send Deauth",
                   command=self.send_deauth).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(deauth_frame, text="Continuous Deauth",
                   command=self.continuous_deauth).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(deauth_frame, text="Stop Deauth",
                   command=self.stop_deauth).grid(row=0, column=4, padx=5, pady=5)

        # Capture status label
        self.capture_status = ttk.Label(
            self.frame, text="Status: Not Capturing", foreground='red'
        )
        self.capture_status.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        # Captured file path (used by crack tab)
        self.captured_file_path = tk.StringVar()

    def load_targets(self, targets):
        """
        Load a list of scanned networks into the target dropdown.
        Called externally by the main app after a scan completes.
        """
        self.target_combo['values'] = targets
        if targets:
            self.target_combo.set(targets[0])
            self._on_target_selected()  # Auto-populate channel for first target

    def _load_targets_prompt(self):
        """Prompt user to go to scan tab if no targets loaded yet."""
        if not self.target_combo['values']:
            messagebox.showinfo("No Networks", "Please scan for networks first.")

    def _on_target_selected(self, event=None):
        """Callback: when target is selected, auto-populate the channel."""
        target = self.target_combo.get()
        if target:
            try:
                # Format: "BSSID - ESSID - CH#"
                parts = target.split(' - ')
                if len(parts) >= 3:
                    channel_part = parts[2].strip()
                    # Extract the channel number from "CH#" format
                    if channel_part.startswith('CH'):
                        channel = channel_part[2:]
                        self.channel_entry.delete(0, 'end')
                        self.channel_entry.insert(0, channel)
                        self.log(f"Channel auto-populated: {channel}")
            except Exception as e:
                self.log(f"Error extracting channel: {e}")

    def get_captured_file(self):
        """Return path to the most recently captured handshake file."""
        return self.captured_file_path.get()

    def start_capture(self):
        """Start WPA2 handshake capture on the selected target."""
        target = self.target_combo.get()
        if not target:
            messagebox.showwarning("No Target", "Please select a target network.")
            return

        bssid   = target.split(' - ')[0]
        channel = self.channel_entry.get().strip()
        device  = self.get_device()

        if not channel:
            messagebox.showwarning("No Channel", "Please select a target or enter channel manually.")
            return

        success, msg = self.capture.start_capture(
            device, bssid, channel,
            on_status=self._update_status,
            on_captured=self._on_handshake_captured
        )
        self.log(msg)

        if success and self.auto_assist_var.get():
            self._start_auto_capture_assist(device, bssid)

    def stop_capture(self):
        """Stop the handshake capture."""
        self.capture.stop_capture()
        self.deauth.stop_continuous_deauth(self.log)
        self._update_status("Status: Not Capturing", "red")
        self.log("Capture stopped.")

    def send_deauth(self):
        """Send a fixed burst of deauth packets."""
        target = self.target_combo.get()
        if not target:
            messagebox.showwarning("No Target", "Please select a target network.")
            return
        bssid  = target.split(' - ')[0]
        device = self.get_device()
        self.deauth.send_deauth(device, bssid, self.packet_count.get().strip(), self.log)

    def continuous_deauth(self):
        """Start continuous deauth attack."""
        target = self.target_combo.get()
        if not target:
            messagebox.showwarning("No Target", "Please select a target network.")
            return
        bssid  = target.split(' - ')[0]
        device = self.get_device()
        self.deauth.start_continuous_deauth(device, bssid, self.log)

    def stop_deauth(self):
        """Stop continuous deauth attack."""
        self.deauth.stop_continuous_deauth(self.log)

    def _update_status(self, text, color):
        """Update the capture status label."""
        self.capture_status.config(text=text, foreground=color)

    def _on_handshake_captured(self, filepath):
        """Callback: called when a handshake .cap file is saved."""
        self.captured_file_path.set(filepath)
        self.log(f"Handshake saved to: {filepath}")

    def _start_auto_capture_assist(self, device, bssid):
        """Send small delayed deauth bursts while capture is active."""

        def assist_worker():
            # Give airodump some warm-up time before first deauth burst.
            schedule = [15, 12, 12]
            for i, wait_seconds in enumerate(schedule, start=1):
                time.sleep(wait_seconds)
                if not self.capture.capturing:
                    return
                self.log(f"Auto-assist: deauth burst {i}/{len(schedule)}")
                self.deauth.send_deauth(device, bssid, "5", self.log)

        threading.Thread(target=assist_worker, daemon=True).start()
