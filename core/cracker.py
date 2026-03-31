"""
core/cracker.py
Handles offline WPA2 password cracking using hashcat.

How it works:
1. Convert the .cap file to .hccapx format (hashcat's input format)
   using cap2hccapx or hcxpcapngtool as a fallback
2. Run hashcat in either:
   - Dictionary mode (-a 0): Try every word in a wordlist file
   - Brute Force mode (-a 3): Try all combinations of a character set
3. Display cracked passwords in the results panel

Hashcat mode 2500 = WPA/WPA2 handshake cracking
"""

import subprocess
import threading
import os
import platform
from tkinter import messagebox
from utils.logger import logger
from utils.validator import validate_length
from utils.commands import build_privileged_cmd, command_exists


# Maps UI charset labels to hashcat mask characters
CHARSET_MAP = {
    'Numbers Only':                     '?d',
    'Letters Only':                     '?l?u',
    'Letters + Numbers':                '?l?u?d',
    'Full (Letters + Numbers + Symbols)': '?l?u?d?s'
}


class PasswordCracker:
    """Cracks WPA2 handshake files using hashcat."""

    def __init__(self):
        self.system = platform.system()
        self.cracking = False

    def start_cracking(self, handshake_file, attack_type, options, on_result, log_callback, on_complete=None):
        """
        Start the password cracking process in a background thread.

        Args:
            handshake_file: Path to the .cap file containing the handshake
            attack_type:    'Brute Force' or 'Dictionary'
            options:        Dict with attack-specific options:
                            Brute force: {'charset', 'min_len', 'max_len'}
                            Dictionary:  {'wordlist'}
            on_result:      Callback(text) to display cracking output
            log_callback:   Function to display status messages
        """
        if self.system != 'Linux':
            messagebox.showinfo("Not Supported", "Password cracking is only supported on Linux.")
            return False

        if not handshake_file or not os.path.exists(handshake_file):
            messagebox.showwarning("No Handshake", "Please select a valid handshake file.")
            return False

        if not attack_type:
            messagebox.showwarning("No Attack Type", "Please select an attack type.")
            return False

        if self.cracking:
            messagebox.showinfo("Cracking In Progress", "A cracking task is already running.")
            return False

        if not command_exists('hashcat'):
            messagebox.showerror("Missing Tool", "hashcat not found. Please install hashcat.")
            return False

        self.cracking = True
        thread = threading.Thread(
            target=self._crack_worker,
            args=(handshake_file, attack_type, options, on_result, log_callback, on_complete),
            daemon=True
        )
        thread.start()
        return True

    def _crack_worker(self, handshake_file, attack_type, options, on_result, log_callback, on_complete=None):
        """
        Background worker that converts the cap file and runs hashcat.
        """
        try:
            # Convert capture to a hashcat-compatible format and mode.
            log_callback("Converting handshake file to hashcat format...")
            hash_file, hash_mode = self._convert_cap(handshake_file)

            # Build the hashcat command based on attack type
            cmd = self._build_command(attack_type, options, hash_file, hash_mode)
            if not cmd:
                return

            log_callback(f"Running hashcat ({attack_type})...")
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Stream output and highlight recovered passwords
            for line in process.stdout:
                if 'RECOVERED' in line:
                    on_result(line)
                    log_callback("Password found! Check results panel.")
            process.wait()

            stderr_text = process.stderr.read() if process.stderr else ""
            if stderr_text.strip() and process.returncode not in (0, 1):
                raise RuntimeError(
                    f"hashcat failed (exit {process.returncode}): {stderr_text.strip().splitlines()[-1]}"
                )

            # Show final cracked results
            show_cmd = build_privileged_cmd(['hashcat', '-m', hash_mode, hash_file, '--show'])
            if not show_cmd:
                log_callback("No privilege escalation tool found (sudo/doas).")
                return

            result = subprocess.run(
                show_cmd,
                capture_output=True, text=True
            )
            if result.stdout:
                on_result("\n=== Cracked Passwords ===\n")
                on_result(result.stdout)
            else:
                on_result("\nNo passwords cracked.\n")

            log_callback("Cracking completed.")
            logger.info("Cracking completed.")

        except Exception as e:
            log_callback(f"Error during cracking: {e}")
            logger.error(f"Cracking error: {e}")
            messagebox.showerror("Error", f"Cracking failed: {e}")
        finally:
            self.cracking = False
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    pass

    def _convert_cap(self, cap_file):
        """
        Convert .cap file into a hashcat-compatible hash file.

        Returns:
            (hash_file_path, hash_mode)

        Preferred format is .22000 (mode 22000) via hcxpcapngtool.
        Falls back to .hccapx (mode 2500) via cap2hccapx.
        """
        base, _ = os.path.splitext(cap_file)
        hash_22000 = f"{base}.22000"
        hash_hccapx = f"{base}.hccapx"

        if command_exists('hcxpcapngtool'):
            hcx_cmd = build_privileged_cmd(['hcxpcapngtool', cap_file, '-o', hash_22000])
            if not hcx_cmd:
                raise RuntimeError("No privilege escalation tool found (sudo/doas).")
            result = subprocess.run(hcx_cmd, capture_output=True, text=True)
            if result.returncode not in (0, 1):
                logger.debug(f"hcxpcapngtool exited with code {result.returncode}: {result.stderr.strip()}")
            if os.path.exists(hash_22000) and os.path.getsize(hash_22000) > 0:
                return hash_22000, '22000'

        if command_exists('cap2hccapx'):
            cap2hccapx_cmd = build_privileged_cmd(['cap2hccapx', cap_file, hash_hccapx])
            if not cap2hccapx_cmd:
                raise RuntimeError("No privilege escalation tool found (sudo/doas).")
            result = subprocess.run(cap2hccapx_cmd, capture_output=True, text=True)
            if result.returncode not in (0, 1):
                logger.debug(f"cap2hccapx exited with code {result.returncode}: {result.stderr.strip()}")
            if os.path.exists(hash_hccapx) and os.path.getsize(hash_hccapx) > 0:
                return hash_hccapx, '2500'

        raise RuntimeError(
            "No converter found. Install hcxtools (hcxpcapngtool) or aircrack-ng-utils (cap2hccapx)."
        )

    def _build_command(self, attack_type, options, hash_file, hash_mode):
        """
        Build the hashcat command based on attack type and options.
        Returns the command list, or None if options are invalid.
        """
        if attack_type == 'Brute Force':
            charset  = CHARSET_MAP.get(options.get('charset', ''), '?l?u?d')
            min_len  = options.get('min_len', '8')
            max_len  = options.get('max_len', '12')

            if not validate_length(min_len, max_len):
                return None

            mask = charset * int(min_len)

            if min_len == max_len:
                return build_privileged_cmd(['hashcat', '-m', hash_mode, hash_file, '-a', '3', mask])
            else:
                return build_privileged_cmd([
                    'hashcat', '-m', hash_mode, hash_file, '-a', '3',
                    '--increment',
                    f'--increment-min={min_len}',
                    f'--increment-max={max_len}',
                    mask
                ])

        elif attack_type == 'Dictionary':
            wordlist = options.get('wordlist', '')
            if not wordlist or not os.path.exists(wordlist):
                messagebox.showerror("Error", "Please select a valid wordlist file.")
                return None
            return build_privileged_cmd(['hashcat', '-m', hash_mode, hash_file, '-a', '0', wordlist])

        return None
