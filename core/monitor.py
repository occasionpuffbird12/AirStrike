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
from utils.commands import build_privileged_cmd, command_exists


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
                # Prefer `iw dev` for accurate interface listing.
                if command_exists('iw'):
                    result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
                    devices = re.findall(r'^\s*Interface\s+(\S+)', result.stdout, re.MULTILINE)
                    if devices:
                        return devices

                # Fallback for older setups.
                result = subprocess.run(['iwconfig'], capture_output=True, text=True)
                devices = []
                for line in result.stdout.splitlines():
                    if 'no wireless extensions' in line:
                        continue
                    if line and not line[0].isspace():
                        devices.append(line.split()[0])
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

        if not command_exists('airmon-ng'):
            log_callback("airmon-ng not found. Install aircrack-ng package.")
            return False

        try:
            # Kill interfering processes before enabling monitor mode
            log_callback("Killing interfering processes (NetworkManager, wpa_supplicant)...")
            check_kill_cmd = build_privileged_cmd(['airmon-ng', 'check', 'kill'])
            start_cmd = build_privileged_cmd(['airmon-ng', 'start', device])
            if not check_kill_cmd or not start_cmd:
                log_callback("No privilege escalation tool found (sudo/doas).")
                return False

            subprocess.run(check_kill_cmd, check=True)
            log_callback("Processes killed. Enabling monitor mode...")

            subprocess.run(start_cmd, check=True)
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

        if not command_exists('airmon-ng'):
            log_callback("airmon-ng not found. Install aircrack-ng package.")
            return False

        try:
            stop_cmd = build_privileged_cmd(['airmon-ng', 'stop', device])
            if not stop_cmd:
                log_callback("No privilege escalation tool found (sudo/doas).")
                return False

            subprocess.run(stop_cmd, check=True)
            self.monitor_mode = False
            logger.info(f"Monitor mode disabled on {device}")
            log_callback(f"Monitor mode disabled on {device}")
            return True
        except Exception as e:
            logger.error(f"Error disabling monitor mode: {e}")
            log_callback(f"Error disabling monitor mode: {e}")
            return False
