"""
utils/commands.py
Command helpers for cross-distro Linux compatibility.

These helpers avoid hardcoding `sudo` so the project can run on distros
that use direct root shells, doas, or sudo.
"""

import os
import shutil


def build_privileged_cmd(base_cmd):
    """
    Build a command with privilege escalation only when needed.

    Preference order when not root: sudo, then doas.
    Returns None if no escalation tool is found.
    """
    if os.geteuid() == 0:
        return list(base_cmd)

    if shutil.which('sudo'):
        return ['sudo'] + list(base_cmd)

    if shutil.which('doas'):
        return ['doas'] + list(base_cmd)

    return None


def command_exists(command_name):
    """Return True if a command is available in PATH."""
    return shutil.which(command_name) is not None
