#!/usr/bin/env python3
"""
AirStrike - WiFi Security Auditing Tool
Author: Security Professional
Version: 3.0
Warning: This tool is for authorized security testing only!

Entry point - run this file to launch AirStrike.
Usage:
    xhost +local:root
    sudo python main.py
"""

import tkinter as tk
from ui.app import AirStrikeApp


def main():
    """Initialize and launch the AirStrike GUI application."""
    root = tk.Tk()
    app = AirStrikeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
