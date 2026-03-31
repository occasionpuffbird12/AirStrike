"""
ui/app.py
Main application window for AirStrike.
Assembles all tabs and the shared console output.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
import threading
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
        self.root.geometry("1280x820")
        self.root.minsize(1120, 720)
        self.root.configure(bg='#0f1720')

        self.style = ttk.Style(self.root)
        self._configure_styles()

        # Show legal disclaimer — exit if user declines
        if not show_disclaimer():
            sys.exit(0)

        # Main layout shell
        self.main = ttk.Frame(self.root, style='Shell.TFrame', padding=(16, 14, 16, 14))
        self.main.pack(fill='both', expand=True)

        self._build_header()

        # Main layout — notebook on top, console on bottom
        self.notebook = ttk.Notebook(self.main, style='Main.TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(10, 10))

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

    def _configure_styles(self):
        """Define the visual theme for the application."""
        self.style.theme_use('clam')

        self.style.configure('Shell.TFrame', background='#0f1720')
        self.style.configure('Card.TFrame', background='#162230')
        self.style.configure('HeaderTitle.TLabel', background='#162230', foreground='#f5fbff',
                             font=('DejaVu Sans', 18, 'bold'))
        self.style.configure('HeaderSub.TLabel', background='#162230', foreground='#8eb2c8',
                             font=('DejaVu Sans', 10))
        self.style.configure('Chip.TLabel', background='#234258', foreground='#d5f2ff',
                             font=('DejaVu Sans', 9, 'bold'), padding=(10, 4))

        self.style.configure('Main.TNotebook', background='#0f1720', borderwidth=0)
        self.style.configure('Main.TNotebook.Tab', background='#1d2e40', foreground='#b9d4e6',
                             padding=(16, 8), font=('DejaVu Sans', 10, 'bold'))
        self.style.map('Main.TNotebook.Tab',
                       background=[('selected', '#2f4f68'), ('active', '#27445d')],
                       foreground=[('selected', '#ffffff'), ('active', '#e9f4fb')])

        self.style.configure('TFrame', background='#142130')
        self.style.configure('TLabelframe', background='#142130', foreground='#d6e6f3',
                             bordercolor='#2a4158', relief='solid')
        self.style.configure('TLabelframe.Label', background='#142130', foreground='#9fc4df',
                             font=('DejaVu Sans', 10, 'bold'))
        self.style.configure('TLabel', background='#142130', foreground='#dce9f4',
                             font=('DejaVu Sans', 10))

        self.style.configure('TButton', background='#2b6f8f', foreground='#f7fbff',
                             borderwidth=0, focusthickness=0, padding=(12, 6),
                             font=('DejaVu Sans', 9, 'bold'))
        self.style.map('TButton', background=[('active', '#3687ac'), ('disabled', '#4a5965')],
                       foreground=[('disabled', '#a9b7c2')])

        self.style.configure('TEntry', fieldbackground='#0f1a24', foreground='#edf7ff',
                             insertcolor='#edf7ff', bordercolor='#34506a', lightcolor='#34506a')
        self.style.configure('TCombobox', fieldbackground='#0f1a24', foreground='#edf7ff',
                             bordercolor='#34506a', lightcolor='#34506a')

        self.style.configure('Treeview', background='#111d28', fieldbackground='#111d28',
                             foreground='#dceaf3', rowheight=26, bordercolor='#2a4158')
        self.style.configure('Treeview.Heading', background='#25435a', foreground='#ebf4fb',
                             font=('DejaVu Sans', 9, 'bold'))
        self.style.map('Treeview', background=[('selected', '#2f607f')])

    def _build_header(self):
        """Build title card for top-level app context."""
        header = ttk.Frame(self.main, style='Card.TFrame', padding=(16, 14))
        header.pack(fill='x')

        ttk.Label(header, text='AirStrike', style='HeaderTitle.TLabel').pack(anchor='w')
        ttk.Label(header, text='Wireless Security Audit Workbench', style='HeaderSub.TLabel').pack(anchor='w')
        ttk.Label(header, text='Linux Authorized Testing Only', style='Chip.TLabel').pack(anchor='e', pady=(6, 0))

    def _build_console(self):
        """Build the shared console output panel at the bottom of the window."""
        console_frame = ttk.LabelFrame(self.main, text="Activity Console", padding=(8, 8))
        console_frame.pack(fill='both', expand=False)

        self.console = scrolledtext.ScrolledText(
            console_frame,
            height=8,
            bg='#0a1016',
            fg='#8be8b6',
            insertbackground='#8be8b6',
            relief='flat',
            font=('DejaVu Sans Mono', 10)
        )
        self.console.pack(fill='both', expand=True, padx=2, pady=2)

    def log(self, message):
        """Write a timestamped message to the console and log file."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        def write_console():
            self.console.insert(tk.END, f"[{timestamp}] {message}\n")
            self.console.see(tk.END)

        if threading.current_thread() is threading.main_thread():
            write_console()
        else:
            self.root.after(0, write_console)

        logger.info(message)

    def _push_networks_to_capture(self):
        """Load discovered networks into the capture tab target dropdown."""
        networks = self.scan_tab.get_networks()
        self.capture_tab.load_targets(networks)
        self.log(f"Loaded {len(networks)} networks into capture tab.")
