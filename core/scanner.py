"""
core/scanner.py
Handles WiFi network discovery using airodump-ng.

Why CSV output instead of stdout?
airodump-ng uses a curses-based terminal UI to display results.
This means its stdout cannot be read line-by-line in Python.
The fix is to use '--output-format csv' which writes results to
a file that we can read and parse every few seconds.

CSV fields (AP lines):
  0: BSSID, 1: First time seen, 2: Last time seen, 3: Channel,
  4: Speed, 5: Privacy (WPA2 etc), 6: Cipher, 7: Authentication,
  8: Power, 9: Beacons, 10: IV, 11: LAN IP, 12: ID-length, 13: ESSID
"""

import subprocess
import threading
import os
import re
import time
import platform
from utils.logger import logger
from utils.validator import validate_device


class NetworkScanner:
    """Scans for nearby WiFi networks using airodump-ng."""

    def __init__(self):
        self.system = platform.system()
        self.scanning = False
        self._scan_thread = None

    def start_scan(self, device, on_network_found, on_complete):
        """
        Start scanning for nearby WiFi networks in a background thread.

        Args:
            device:           Wireless interface in monitor mode
            on_network_found: Callback(bssid, channel, essid, security)
                              called for each new network found
            on_complete:      Callback() called when scan finishes
        """
        if self.scanning:
            return
        if not validate_device(device):
            return

        self.scanning = True
        self._scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(device, on_network_found, on_complete),
            daemon=True
        )
        self._scan_thread.start()

    def stop_scan(self):
        """Signal the scan to stop."""
        self.scanning = False

    def _scan_worker(self, device, on_network_found, on_complete):
        """
        Background worker that runs airodump-ng and parses the CSV output.
        Runs for up to 60 seconds or until stop_scan() is called.
        """
        csv_prefix = "/tmp/airstrike_scan"
        csv_path   = f"{csv_prefix}-01.csv"
        process    = None

        try:
            # Remove any leftover CSV from a previous scan
            if os.path.exists(csv_path):
                os.remove(csv_path)

            # Launch airodump-ng with CSV file output
            # stdout/stderr suppressed — airodump-ng uses curses UI, not plain text
            process = subprocess.Popen(
                ['sudo', 'airodump-ng', '--output-format', 'csv', '-w', csv_prefix, device],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            seen_bssids = set()   # Prevent duplicate entries in the results table
            start_time  = time.time()

            while self.scanning and (time.time() - start_time) < 60:
                time.sleep(2)

                if not os.path.exists(csv_path):
                    continue

                try:
                    self._parse_csv(csv_path, seen_bssids, on_network_found)
                except Exception as e:
                    logger.error(f"CSV parse error: {e}")

        except Exception as e:
            logger.error(f"Scan error: {e}")
        finally:
            if process:
                process.terminate()
            self.scanning = False
            on_complete()

    def _parse_csv(self, csv_path, seen_bssids, on_network_found):
        """
        Parse the airodump-ng CSV output file and extract AP information.
        Calls on_network_found for each new network discovered.
        """
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            # Skip empty lines, column headers, and the station section header
            if not line or line.startswith('BSSID') or line.startswith('Station MAC'):
                continue

            parts = [p.strip() for p in line.split(',')]

            # AP lines have at least 14 comma-separated fields
            if len(parts) < 14:
                continue

            bssid = parts[0]

            # Validate it looks like a real MAC address
            if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
                continue

            # Skip networks already added to the results table
            if bssid in seen_bssids:
                continue

            channel  = parts[3].strip()
            security = parts[5].strip()
            essid    = parts[13].strip() if parts[13].strip() else "Hidden"

            seen_bssids.add(bssid)
            on_network_found(bssid, channel, essid, security)
            logger.info(f"Found: {essid} [{bssid}] CH{channel} {security}")
