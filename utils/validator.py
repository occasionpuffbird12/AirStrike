"""
utils/validator.py
Input validation functions for AirStrike.
All user inputs are validated here before being passed to system commands
to prevent command injection and invalid operations.
"""

import re
from tkinter import messagebox


def validate_device(device):
    """
    Validate wireless device name.
    Only allows alphanumeric characters, hyphens, and underscores
    to prevent shell command injection.
    """
    if not device:
        messagebox.showwarning("No Device", "Please select a wireless device.")
        return False
    if not re.match(r'^[\w\-]+$', device):
        messagebox.showerror("Invalid Device", "Device name contains invalid characters.")
        return False
    return True


def validate_bssid(bssid):
    """
    Validate BSSID (MAC address) format.
    Expected format: XX:XX:XX:XX:XX:XX (e.g. 00:1A:2B:3C:4D:5E)
    """
    if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
        messagebox.showerror("Invalid BSSID", "BSSID must be in format XX:XX:XX:XX:XX:XX")
        return False
    return True


def validate_channel(channel):
    """
    Validate WiFi channel number.
    Accepts channels 1-165 to cover both 2.4GHz (1-14) and 5GHz (36-165) bands.
    """
    if not channel.isdigit():
        messagebox.showerror("Invalid Channel", "Channel must be a number.")
        return False
    ch = int(channel)
    if ch < 1 or ch > 165:
        messagebox.showerror("Invalid Channel", "Channel must be between 1 and 165.")
        return False
    return True


def validate_packet_count(packet_count):
    """
    Validate deauth packet count.
    Must be a positive integer.
    """
    if not packet_count.isdigit():
        messagebox.showerror("Invalid Input", "Packet count must be a number.")
        return False
    return True


def validate_length(min_len, max_len):
    """
    Validate brute force min/max password length.
    Both must be positive integers.
    """
    if not (min_len.isdigit() and max_len.isdigit()):
        messagebox.showerror("Invalid Input", "Min/Max length must be numbers.")
        return False
    return True
