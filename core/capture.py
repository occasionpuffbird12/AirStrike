"""
core/capture.py
Handles WPA2 4-way handshake capture using airodump-ng.

What is a WPA2 handshake?
When a client connects to a WPA2 network, it performs a 4-way handshake
with the access point to authenticate. This handshake contains enough
information to attempt offline password cracking without being connected
to the network.

How capture works:
1. Lock the adapter to the target channel using iwconfig
2. Run airodump-ng filtered to the target BSSID and channel
3. Wait for a client to connect (or use deauth to force reconnection)
4. Detect the .cap file being written by airodump-ng
"""

import subprocess
import threading
import os
import time
import platform
import re
from datetime import datetime
from pathlib import Path
from utils.logger import logger
from utils.validator import validate_device, validate_bssid, validate_channel
from utils.commands import build_privileged_cmd, command_exists


class HandshakeCapture:
    """Captures the WPA2 4-way handshake from a target network."""

    def __init__(self):
        self.system = platform.system()
        self.capturing = False
        self.capture_process = None
        self.capture_file = None
        self.captures_dir = self._ensure_captures_dir()

    def _ensure_captures_dir(self):
        """Create and return the captures directory path in the AirStrike folder."""
        # Get the AirStrike project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        captures_dir = os.path.join(project_root, "captures")
        Path(captures_dir).mkdir(parents=True, exist_ok=True)
        return captures_dir

    def start_capture(self, device, bssid, channel, on_status, on_captured):
        """
        Start handshake capture in a background thread.

        Args:
            device:      Wireless interface in monitor mode
            bssid:       Target network MAC address
            channel:     Target network channel
            on_status:   Callback(message, color) for status updates
            on_captured: Callback(filepath) called when handshake is saved
        """
        if self.system != 'Linux':
            return False, "Handshake capture is only supported on Linux."

        if not command_exists('airodump-ng'):
            return False, "airodump-ng not found. Install aircrack-ng package."

        if not command_exists('aircrack-ng'):
            return False, "aircrack-ng not found. Install aircrack-ng package."

        if self.capturing:
            return False, "Capture is already in progress."

        if not validate_device(device): return False, "Invalid device."
        if not validate_bssid(bssid):   return False, "Invalid BSSID."
        if not validate_channel(channel): return False, "Invalid channel."

        self.capturing = True
        on_status("Status: Capturing Handshake...", "orange")

        thread = threading.Thread(
            target=self._capture_worker,
            args=(device, bssid, channel, on_status, on_captured),
            daemon=True
        )
        thread.start()
        return True, "Capture started."

    def stop_capture(self):
        """Stop the handshake capture process."""
        self.capturing = False
        if self.capture_process:
            self.capture_process.terminate()

    def _capture_worker(self, device, bssid, channel, on_status, on_captured):
        """
        Background worker that runs airodump-ng targeted at one network.
        Polls every 2 seconds for the .cap file with valid handshake data.
        Times out after 5 minutes if no handshake captured.
        """
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_file = os.path.join(self.captures_dir, f"handshake_{timestamp}")
        start_time   = time.time()
        timeout_secs = 300  # 5 minutes

        try:
            # Lock the adapter to channel (prefer modern `iw`, fallback to `iwconfig`).
            if command_exists('iw'):
                set_channel_cmd = build_privileged_cmd(['iw', 'dev', device, 'set', 'channel', channel])
            else:
                set_channel_cmd = build_privileged_cmd(['iwconfig', device, 'channel', channel])

            if not set_channel_cmd:
                raise RuntimeError("No privilege escalation tool found (sudo/doas).")

            subprocess.run(set_channel_cmd, check=True)

            # Run airodump-ng focused on the target BSSID and channel
            cmd = build_privileged_cmd([
                'airodump-ng', '--bssid', bssid, '-c', channel, '-w', capture_file, device
            ])
            if not cmd:
                raise RuntimeError("No privilege escalation tool found (sudo/doas).")
            self.capture_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            logger.info(f"Capturing handshake on {bssid} channel {channel}...")
            logger.info(f"Capture file: {capture_file}-01.cap")
            logger.info(f"Timeout: {timeout_secs} seconds")

            checked_count = 0
            last_checked_cap_size = -1
            # Poll for the .cap file with valid handshake data every 2 seconds
            while self.capturing:
                elapsed = time.time() - start_time
                if elapsed > timeout_secs:
                    logger.warning(f"Capture timeout after {timeout_secs}s - no handshake detected")
                    on_status("Status: Timeout - No handshake captured", "red")
                    break

                time.sleep(2)
                cap_path = f"{capture_file}-01.cap"
                csv_path = f"{capture_file}-01.csv"
                checked_count += 1

                # Log file status for debugging
                cap_exists = os.path.exists(cap_path)
                csv_exists = os.path.exists(csv_path)

                if cap_exists or csv_exists:
                    cap_size = os.path.getsize(cap_path) if cap_exists else 0
                    csv_size = os.path.getsize(csv_path) if csv_exists else 0
                    logger.debug(f"Check #{checked_count}: CAP={cap_size}B CSV={csv_size}B")

                    if cap_exists and cap_size > 0 and cap_size != last_checked_cap_size:
                        last_checked_cap_size = cap_size
                        if self._has_handshake(cap_path, bssid):
                            logger.info("Handshake captured successfully!")
                            on_status("Status: Handshake Captured!", "green")
                            on_captured(cap_path)
                            break

        except Exception as e:
            logger.error(f"Capture error: {e}")
            on_status("Status: Error", "red")
        finally:
            if self.capture_process:
                self.capture_process.terminate()
            self.capturing = False

    def _has_handshake(self, cap_path, target_bssid):
        """
        Validate the capture file with aircrack-ng.
        CSV output does not reliably include handshake state, but aircrack-ng
        reports it as e.g. 'WPA (1 handshake)'.
        """
        if not os.path.exists(cap_path):
            return False

        try:
            result = subprocess.run(
                ['aircrack-ng', cap_path],
                capture_output=True,
                text=True,
                timeout=20
            )
            output = f"{result.stdout}\n{result.stderr}".upper()

            # Match target line that includes handshake count in aircrack output.
            # Example: D2:11:...  Realme 11 Pro 5G  WPA (1 handshake)
            handshake_re = re.compile(
                rf"{re.escape(target_bssid.upper())}.*WPA\d?\s*\(\s*(\d+)\s+HANDSHAKES?\s*\)",
                re.IGNORECASE | re.DOTALL
            )

            match = handshake_re.search(output)
            if match and int(match.group(1)) > 0:
                logger.info(f"WPA Handshake detected in CAP for {target_bssid}")
                return True
        except Exception as e:
            logger.debug(f"Error validating handshake from CAP: {e}")

        return False
