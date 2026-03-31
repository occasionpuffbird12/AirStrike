"""
ui/scan_tab.py
Network Scan tab UI.
Displays discovered WiFi networks and connected stations in separate tables.
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
        self.log          = log_callback
        self.get_device   = get_device_callback
        self.scanner      = NetworkScanner()
        self.on_scan_done = None  # Set by app.py to push networks to capture tab

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Network Scan")
        self._build_ui()

    def _build_ui(self):
        """Build all widgets for the Network Scan tab."""
        # Scan control buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=5)

        ttk.Button(btn_frame, text="Start Scan",
                   command=self.start_scan).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Stop Scan",
                   command=self.stop_scan).pack(side='left', padx=5)

        # --- Access Points table ---
        ttk.Label(self.frame, text="Access Points (Networks):").grid(
            row=1, column=0, columnspan=3, sticky='w', padx=5
        )
        self.network_tree = ttk.Treeview(
            self.frame,
            columns=('BSSID', 'Channel', 'ESSID', 'Security'),
            show='headings',
            height=8
        )
        for col in ('BSSID', 'Channel', 'ESSID', 'Security'):
            self.network_tree.heading(col, text=col)
            self.network_tree.column(col, width=160)
        self.network_tree.grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky='nsew')

        ap_scroll = ttk.Scrollbar(self.frame, orient='vertical',
                                   command=self.network_tree.yview)
        ap_scroll.grid(row=2, column=2, sticky='ns')
        self.network_tree.configure(yscrollcommand=ap_scroll.set)

        # --- Connected Stations table ---
        ttk.Label(self.frame, text="Connected Stations (Clients):").grid(
            row=3, column=0, columnspan=3, sticky='w', padx=5, pady=(10, 0)
        )
        self.station_tree = ttk.Treeview(
            self.frame,
            columns=('Station MAC', 'Associated BSSID', 'Power', 'Probes'),
            show='headings',
            height=6
        )
        col_widths = {'Station MAC': 160, 'Associated BSSID': 160, 'Power': 70, 'Probes': 200}
        for col in ('Station MAC', 'Associated BSSID', 'Power', 'Probes'):
            self.station_tree.heading(col, text=col)
            self.station_tree.column(col, width=col_widths[col])
        self.station_tree.grid(row=4, column=0, columnspan=2, padx=5, pady=2, sticky='nsew')

        st_scroll = ttk.Scrollbar(self.frame, orient='vertical',
                                   command=self.station_tree.yview)
        st_scroll.grid(row=4, column=2, sticky='ns')
        self.station_tree.configure(yscrollcommand=st_scroll.set)

        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

    def start_scan(self):
        """Start scanning for nearby WiFi networks and clients."""
        device = self.get_device()
        # Clear previous results
        for item in self.network_tree.get_children():
            self.network_tree.delete(item)
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)

        self.log("Starting network scan...")
        self.scanner.start_scan(
            device,
            on_network_found=self._on_network_found,
            on_station_found=self._on_station_found,
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
        """Callback: add a newly discovered AP to the networks table."""
        self.network_tree.insert('', 'end', values=(bssid, channel, essid, security))
        self.log(f"Found AP: {essid} [{bssid}] CH{channel} {security}")

    def _on_station_found(self, station_mac, bssid, power, probes):
        """Callback: add a newly discovered client to the stations table."""
        self.station_tree.insert('', 'end', values=(station_mac, bssid, power, probes))
        self.log(f"Found Station: {station_mac} → {bssid} PWR:{power}")

    def _on_scan_complete(self):
        """Callback: called when scan finishes. Pushes networks to capture tab."""
        self.log("Scan completed.")
        # Notify app.py to load networks into the capture tab target dropdown
        if self.on_scan_done:
            self.on_scan_done()