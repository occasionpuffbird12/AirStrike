"""
core/scanner.py
Handles WiFi network discovery using airodump-ng.

Why CSV output instead of stdout?
airodump-ng uses a curses-based terminal UI to display results.
This means its stdout cannot be read line-by-line in Python.
The fix is to use '--output-format csv' which writes results to
a file that we can read and parse every few seconds.

CSV AP fields:
  0: BSSID, 1: First time seen, 2: Last time seen, 3: Channel,
  4: Speed, 5: Privacy (WPA2 etc), 6: Cipher, 7: Authentication,
  8: Power, 9: Beacons, 10: IV, 11: LAN IP, 12: ID-length, 13: ESSID

CSV Station fields:
  0: Station MAC, 1: First time seen, 2: Last time seen, 3: Power,
  4: # packets, 5: BSSID, 6: Probes
"""

import subprocess
import threading
import os
import re
import time
import platform
from utils.logger import logger
from utils.validator import validate_device
from utils.commands import build_privileged_cmd, command_exists


class NetworkScanner:
    """Scans for nearby WiFi networks and connected stations using airodump-ng."""

    def __init__(self):
        self.system = platform.system()
        self.scanning = False
        self._scan_thread = None

    def start_scan(self, device, on_network_found, on_station_found, on_complete):
        """
        Start scanning for nearby WiFi networks in a background thread.

        Args:
            device:           Wireless interface in monitor mode
            on_network_found: Callback(bssid, channel, essid, security)
            on_station_found: Callback(station_mac, bssid, power, probes)
            on_complete:      Callback() called when scan finishes
        """
        if self.scanning:
            return
        if not validate_device(device):
            return
        if not command_exists('airodump-ng'):
            logger.error("airodump-ng not found. Install aircrack-ng package.")
            return

        self.scanning = True
        self._scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(device, on_network_found, on_station_found, on_complete),
            daemon=True
        )
        self._scan_thread.start()

    def stop_scan(self):
        """Signal the scan to stop."""
        self.scanning = False

    def _scan_worker(self, device, on_network_found, on_station_found, on_complete):
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
            scan_cmd = build_privileged_cmd([
                'airodump-ng', '--output-format', 'csv', '-w', csv_prefix, device
            ])
            if not scan_cmd:
                logger.error("No privilege escalation tool found (sudo/doas).")
                return

            process = subprocess.Popen(
                scan_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            seen_bssids   = set()  # Prevent duplicate AP entries
            seen_stations = set()  # Prevent duplicate station entries
            start_time    = time.time()

            while self.scanning and (time.time() - start_time) < 60:
                time.sleep(2)

                if not os.path.exists(csv_path):
                    continue

                try:
                    self._parse_csv(
                        csv_path, seen_bssids, seen_stations,
                        on_network_found, on_station_found
                    )
                except Exception as e:
                    logger.error(f"CSV parse error: {e}")

        except Exception as e:
            logger.error(f"Scan error: {e}")
        finally:
            if process:
                process.terminate()
            self.scanning = False
            on_complete()

    def _parse_csv(self, csv_path, seen_bssids, seen_stations,
                   on_network_found, on_station_found):
        """
        Parse airodump-ng CSV output.
        The CSV has two sections separated by a blank line:
        1. Access Points (APs)
        2. Connected Stations (clients)
        """
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        in_station_section = False

        for line in lines:
            line = line.strip()

            # Blank line separates AP section from Station section
            if not line:
                continue

            # Detect start of station section
            if line.startswith('Station MAC'):
                in_station_section = True
                continue

            # Skip AP section header
            if line.startswith('BSSID'):
                in_station_section = False
                continue

            parts = [p.strip() for p in line.split(',')]

            if in_station_section:
                # Parse connected station entry
                # Fields: Station MAC, First seen, Last seen, Power, Packets, BSSID, Probes
                if len(parts) < 6:
                    continue
                station_mac = parts[0]
                if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', station_mac):
                    continue
                if station_mac in seen_stations:
                    continue

                power       = parts[3].strip()
                bssid       = parts[5].strip()
                probes      = parts[6].strip() if len(parts) > 6 else ""

                seen_stations.add(station_mac)
                on_station_found(station_mac, bssid, power, probes)

            else:
                # Parse AP entry
                if len(parts) < 14:
                    continue
                bssid = parts[0]
                if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
                    continue
                if bssid in seen_bssids:
                    continue

                channel  = parts[3].strip()
                security = parts[5].strip()
                essid    = parts[13].strip() if parts[13].strip() else "Hidden"

                seen_bssids.add(bssid)
                on_network_found(bssid, channel, essid, security)