"""
ui/app.py
Main application window for AirStrike.
Assembles all tabs and the shared console output.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from datetime import datetime

from utils.disclaimer import show_disclaimer
from utils.logger import logger
from ui.device_tab import DeviceTab
from ui.scan_tab import ScanTab
from ui.capture_tab import CaptureTab
from ui.crack_tab import CrackTab


class AirStrikeApp:
    """Main AirStrike application — builds the window and all tabs."""

    def __init__(self, root):
        self.root = root
        self.root.title("AirStrike - WiFi Security Auditing Tool v3.0")
        self.root.geometry("1200x750")
        self.root.configure(bg='#2c3e50')

        # Show legal disclaimer — exit if user declines
        if not show_disclaimer():
            sys.exit(0)

        # Main layout — notebook on top, console on bottom
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Build console panel (must exist before tabs so log() works)
        self._build_console()

        # Create all tabs — pass shared callbacks between them
        self.device_tab  = DeviceTab(self.notebook, self.log)
        self.scan_tab    = ScanTab(self.notebook, self.device_tab.get_device, self.log)
        self.capture_tab = CaptureTab(self.notebook, self.device_tab.get_device, self.log)
        self.crack_tab   = CrackTab(self.notebook, self.capture_tab.get_captured_file, self.log)

        # Wire up: when scan completes, auto-push networks into capture tab
        self.scan_tab.on_scan_done = self._push_networks_to_capture

        self.log("AirStrike v3.0 ready.")
        logger.info("AirStrike v3.0 started.")

    def _build_console(self):
        """Build the shared console output panel at the bottom of the window."""
        console_frame = ttk.LabelFrame(self.root, text="Console Output")
        console_frame.pack(fill='both', expand=False, padx=5, pady=5)

        self.console = scrolledtext.ScrolledText(
            console_frame, height=8, bg='black', fg='#00ff00'
        )
        self.console.pack(fill='both', expand=True, padx=5, pady=5)

    def log(self, message):
        """Write a timestamped message to the console and log file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        logger.info(message)

    def _push_networks_to_capture(self):
        """Load discovered networks into the capture tab target dropdown."""
        networks = self.scan_tab.get_networks()
        self.capture_tab.load_targets(networks)
        self.log(f"Loaded {len(networks)} networks into capture tab.")
