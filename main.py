#!/usr/bin/env python3
"""
AirStrike - WiFi Security Auditing Tool
Author: Security Professional
Version: 3.0
Warning: This tool is for authorized security testing only!

Entry point - run this file to launch AirStrike.
Usage:
    sudo python main.py
"""

import os
import subprocess
import sys
import tkinter as tk
from ui.app import AirStrikeApp


def fix_display_permissions():
    """
    Fix X display permissions when running with sudo.

    Problem:
        When you run 'sudo python main.py', the process switches to root.
        Root user does not have access to the X11 display session by default,
        which causes the 'couldn't connect to display' error.

    Solution:
        Detect the original user (stored in SUDO_USER environment variable)
        and run 'xhost +local:root' as that user to grant root access
        to the display. This is done automatically so the user never
        has to type it manually.

    Compatibility:
        Works on all X11-based Linux distros:
        Kali, Ubuntu, Parrot, Debian, Fedora, Arch, Manjaro, etc.
        Will not work on pure Wayland sessions (rare on security distros).
    """
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        try:
            subprocess.run(
                ['sudo', '-u', sudo_user, 'xhost', '+local:root'],
                capture_output=True
            )
        except Exception as e:
            print(f"[Warning] Could not set display permissions: {e}")
            print("If GUI fails, run manually: xhost +local:root")


def check_root():
    """
    Ensure AirStrike is running with root privileges.
    Root is required for monitor mode, packet injection, and raw socket access.
    """
    if os.geteuid() != 0:
        print("[-] AirStrike requires root privileges.")
        print("    Run with: sudo python main.py")
        sys.exit(1)


def main():
    """Main entry point - initialize and launch AirStrike."""
    check_root()               # Must be root
    fix_display_permissions()  # Auto-fix X display for sudo
    root = tk.Tk()
    app = AirStrikeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()