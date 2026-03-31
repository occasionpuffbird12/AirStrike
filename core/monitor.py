"""
core/monitor.py
Handles wireless device management and monitor mode control.

Monitor mode allows the WiFi adapter to capture ALL wireless packets
in range, not just packets addressed to it. This is required for
network scanning and handshake capture.

Key commands used:
- iwconfig              : list and inspect wireless interfaces
- airmon-ng check kill  : kill processes that interfere with monitor mode
- airmon-ng start       : enable monitor mode on a device
- airmon-ng stop        : disable monitor mode and return to managed mode
"""

import subprocess
import platform
import re
import time
from utils.logger import logger
from utils.validator import validate_device


class MonitorController:
    """Manages wireless device selection and monitor mode toggling."""

    def __init__(self):
        self.system = platform.system()
        self.monitor_mode = False

    def get_devices(self):
        """
        Scan for available wireless network interfaces.
        Returns a list of device names (e.g. ['wlan0', 'wlp0s20f3mon']).
        """
        try:
            if self.system == 'Linux':
                result = subprocess.run(['iwconfig'], capture_output=True, text=True)
                devices = re.findall(r'^(\w+)', result.stdout, re.MULTILINE)
                return devices
            else:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True, text=True, check=True
                )
                return re.findall(r'Name\s*:\s*(.+)', result.stdout)
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []

    def get_device_info(self, device):
        """
        Get detailed information about a specific wireless device.
        Returns raw output from iwconfig or netsh as a string.
        """
        try:
            if self.system == 'Linux':
                result = subprocess.run(['iwconfig', device], capture_output=True, text=True)
                return result.stdout
            else:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interface', device],
                    capture_output=True, text=True
                )
                return result.stdout
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return f"Error: {e}"

    def enable_monitor_mode(self, device, log_callback):
        """
        Enable monitor mode on the given wireless device.

        Step 1: Kill interfering processes (NetworkManager, wpa_supplicant)
                using 'airmon-ng check kill'. Without this step, these
                processes keep changing channels and break scanning.
        Step 2: Enable monitor mode using 'airmon-ng start <device>'.

        Returns True on success, False on failure.
        """
        if self.system != 'Linux':
            log_callback("Monitor mode is only supported on Linux.")
            return False

        if not validate_device(device):
            return False

        try:
            # Kill interfering processes before enabling monitor mode
            log_callback("Killing interfering processes (NetworkManager, wpa_supplicant)...")
            subprocess.run(['sudo', 'airmon-ng', 'check', 'kill'], check=True)
            log_callback("Processes killed. Enabling monitor mode...")

            subprocess.run(['sudo', 'airmon-ng', 'start', device], check=True)
            self.monitor_mode = True
            logger.info(f"Monitor mode enabled on {device}")
            log_callback(f"Monitor mode enabled on {device}")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"Error enabling monitor mode: {e}")
            log_callback(f"Error enabling monitor mode: {e}")
            return False

    def disable_monitor_mode(self, device, log_callback):
        """
        Disable monitor mode and return device to managed mode.
        Returns True on success, False on failure.
        """
        if self.system != 'Linux':
            return False

        if not validate_device(device):
            return False

        try:
            subprocess.run(['sudo', 'airmon-ng', 'stop', device], check=True)
            self.monitor_mode = False
            logger.info(f"Monitor mode disabled on {device}")
            log_callback(f"Monitor mode disabled on {device}")
            return True
        except Exception as e:
            logger.error(f"Error disabling monitor mode: {e}")
            log_callback(f"Error disabling monitor mode: {e}")
            return False
