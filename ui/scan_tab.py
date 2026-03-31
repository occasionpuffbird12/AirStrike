"""
ui/scan_tab.py
Network Scan tab UI.
Displays discovered WiFi networks in a table.
Talks to core/scanner.py for all backend operations.
"""

import tkinter as tk
from tkinter import ttk
from core.scanner import NetworkScanner


class ScanTab:
    """Builds and manages the Network Scan tab."""

    def __init__(self, notebook, get_device_callback, log_callback):
        """
        Args:
            notebook:            The ttk.Notebook to attach this tab to
            get_device_callback: Function that returns the selected device name
            log_callback:        Function to write messages to the console
        """
        self.log        = log_callback
        self.get_device = get_device_callback
        self.scanner    = NetworkScanner()

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Network Scan")
        self._build_ui()

    def _build_ui(self):
        """Build all widgets for the Network Scan tab."""
        # Scan control buttons
        ttk.Button(self.frame, text="Start Scan",
                   command=self.start_scan).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(self.frame, text="Stop Scan",
                   command=self.stop_scan).grid(row=0, column=1, padx=5, pady=5)

        # Network results table with columns
        self.network_tree = ttk.Treeview(
            self.frame,
            columns=('BSSID', 'Channel', 'ESSID', 'Security'),
            show='headings'
        )
        for col in ('BSSID', 'Channel', 'ESSID', 'Security'):
            self.network_tree.heading(col, text=col)
        self.network_tree.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        # Scrollbar for the results table
        scrollbar = ttk.Scrollbar(self.frame, orient='vertical',
                                   command=self.network_tree.yview)
        scrollbar.grid(row=1, column=2, sticky='ns')
        self.network_tree.configure(yscrollcommand=scrollbar.set)

        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def start_scan(self):
        """Start scanning for nearby WiFi networks."""
        device = self.get_device()
        # Clear previous results
        for item in self.network_tree.get_children():
            self.network_tree.delete(item)

        self.log("Starting network scan...")
        self.scanner.start_scan(
            device,
            on_network_found=self._on_network_found,
            on_complete=self._on_scan_complete
        )

    def stop_scan(self):
        """Stop the network scan."""
        self.scanner.stop_scan()
        self.log("Scan stopped.")

    def get_networks(self):
        """Return list of scanned networks as 'BSSID - ESSID' strings."""
        targets = []
        for item in self.network_tree.get_children():
            values = self.network_tree.item(item)['values']
            if values:
                targets.append(f"{values[0]} - {values[2]}")
        return targets

    def _on_network_found(self, bssid, channel, essid, security):
        """Callback: add a newly discovered network to the results table."""
        self.network_tree.insert('', 'end', values=(bssid, channel, essid, security))
        self.log(f"Found: {essid} [{bssid}] CH{channel} {security}")

    def _on_scan_complete(self):
        """Callback: called when the scan finishes or times out."""
        self.log("Scan completed.")
