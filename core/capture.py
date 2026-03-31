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
from datetime import datetime
from utils.logger import logger
from utils.validator import validate_device, validate_bssid, validate_channel


class HandshakeCapture:
    """Captures the WPA2 4-way handshake from a target network."""

    def __init__(self):
        self.system = platform.system()
        self.capturing = False
        self.capture_process = None
        self.capture_file = None

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
        Polls every 2 seconds for the .cap file to appear.
        """
        timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_file = f"/tmp/handshake_{timestamp}"

        try:
            # Lock the wireless adapter to the target channel
            subprocess.run(['sudo', 'iwconfig', device, 'channel', channel], check=True)

            # Run airodump-ng focused on the target BSSID and channel
            cmd = ['sudo', 'airodump-ng', '--bssid', bssid, '-c', channel,
                   '-w', capture_file, device]
            self.capture_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            logger.info(f"Capturing handshake on {bssid} channel {channel}...")

            # Poll for the .cap file every 2 seconds
            while self.capturing:
                time.sleep(2)
                cap_path = f"{capture_file}-01.cap"
                if os.path.exists(cap_path):
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
