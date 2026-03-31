"""
ui/device_tab.py
Device Management tab UI.
Handles wireless interface selection and monitor mode controls.
Talks to core/monitor.py for all backend operations.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from core.monitor import MonitorController


class DeviceTab:
    """Builds and manages the Device Management tab."""

    def __init__(self, notebook, log_callback):
        """
        Args:
            notebook:     The ttk.Notebook to attach this tab to
            log_callback: Function to write messages to the console
        """
        self.log = log_callback
        self.monitor = MonitorController()

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Device Management")
        self._build_ui()

    def _build_ui(self):
        """Build all widgets for the Device Management tab."""
        # Device selection row
        ttk.Label(self.frame, text="WiFi Device:").grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        self.device_combo = ttk.Combobox(self.frame, width=30)
        self.device_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Refresh Devices",
                   command=self.refresh_devices).grid(row=0, column=2, padx=5, pady=5)

        # Device info display
        ttk.Label(self.frame, text="Device Info:").grid(
            row=1, column=0, padx=5, pady=5, sticky='nw'
        )
        self.device_info = scrolledtext.ScrolledText(self.frame, height=10, width=60)
        self.device_info.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        # Monitor mode status and controls
        ttk.Label(self.frame, text="Monitor Mode:").grid(
            row=2, column=0, padx=5, pady=5, sticky='w'
        )
        self.monitor_status = ttk.Label(self.frame, text="Status: OFF", foreground='red')
        self.monitor_status.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        ttk.Button(self.frame, text="Enable Monitor Mode",
                   command=self.enable_monitor).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Disable Monitor Mode",
                   command=self.disable_monitor).grid(row=3, column=1, padx=5, pady=5)

    def get_device(self):
        """Return the currently selected device name."""
        return self.device_combo.get()

    def refresh_devices(self):
        """Refresh the device dropdown with available wireless interfaces."""
        devices = self.monitor.get_devices()
        self.device_combo['values'] = devices
        if devices:
            self.device_combo.set(devices[0])
            info = self.monitor.get_device_info(devices[0])
            self.device_info.delete(1.0, tk.END)
            self.device_info.insert(1.0, info)

    def enable_monitor(self):
        """Enable monitor mode on the selected device."""
        device = self.get_device()
        success = self.monitor.enable_monitor_mode(device, self.log)
        if success:
            self.monitor_status.config(text="Status: ON", foreground='green')
            self.refresh_devices()
        else:
            messagebox.showerror("Error", "Failed to enable monitor mode.")

    def disable_monitor(self):
        """Disable monitor mode on the selected device."""
        device = self.get_device()
        success = self.monitor.disable_monitor_mode(device, self.log)
        if success:
            self.monitor_status.config(text="Status: OFF", foreground='red')
            self.refresh_devices()
