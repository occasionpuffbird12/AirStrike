"""
utils/disclaimer.py
Legal disclaimer prompt for AirStrike.

Shows an ethical use agreement before the tool launches.
This is the industry standard approach used by professional
penetration testing tools like Metasploit.

Why not a password?
- AirStrike is open source — a hardcoded password is visible to anyone
- A legal disclaimer makes the user take responsibility
- This is how real security tools handle authorization
"""

from tkinter import messagebox
from utils.logger import logger


def show_disclaimer():
    """
    Display the legal disclaimer dialog.
    Returns True if the user accepts, False if they decline.
    The tool will exit if the user declines.
    """
    response = messagebox.askyesno(
        "Legal Disclaimer",
        "⚠️  WARNING - Authorized Use Only\n\n"
        "AirStrike is intended for authorized security testing only.\n\n"
        "By clicking YES you confirm that:\n"
        "  • You own the network you are testing, OR\n"
        "  • You have explicit written permission to test it\n"
        "  • You understand unauthorized access is illegal\n"
        "  • You take full responsibility for your actions\n\n"
        "Unauthorized use may violate local and international laws.\n\n"
        "Do you agree and wish to continue?"
    )
    if response:
        logger.info("User accepted legal disclaimer.")
    else:
        logger.info("User declined disclaimer. Exiting.")
    return response
