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

    def start_cracking(self, handshake_file, attack_type, options, on_result, log_callback):
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
            return

        if not handshake_file or not os.path.exists(handshake_file):
            messagebox.showwarning("No Handshake", "Please select a valid handshake file.")
            return

        if not attack_type:
            messagebox.showwarning("No Attack Type", "Please select an attack type.")
            return

        thread = threading.Thread(
            target=self._crack_worker,
            args=(handshake_file, attack_type, options, on_result, log_callback),
            daemon=True
        )
        thread.start()

    def _crack_worker(self, handshake_file, attack_type, options, on_result, log_callback):
        """
        Background worker that converts the cap file and runs hashcat.
        """
        try:
            hccapx_file = handshake_file.replace('.cap', '.hccapx')

            # Convert .cap to hashcat format
            log_callback("Converting handshake file to hashcat format...")
            self._convert_cap(handshake_file, hccapx_file)

            # Build the hashcat command based on attack type
            cmd = self._build_command(attack_type, options, hccapx_file)
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

            # Show final cracked results
            result = subprocess.run(
                ['sudo', 'hashcat', '-m', '2500', hccapx_file, '--show'],
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

    def _convert_cap(self, cap_file, hccapx_file):
        """
        Convert .cap file to .hccapx format for hashcat.
        Tries cap2hccapx first, falls back to hcxpcapngtool.
        """
        try:
            subprocess.run(
                ['sudo', 'cap2hccapx', cap_file, hccapx_file],
                check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                ['sudo', 'hcxpcapngtool', cap_file, '-o', hccapx_file],
                check=True
            )

    def _build_command(self, attack_type, options, hccapx_file):
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
                return ['sudo', 'hashcat', '-m', '2500', hccapx_file, '-a', '3', mask]
            else:
                return [
                    'sudo', 'hashcat', '-m', '2500', hccapx_file, '-a', '3',
                    '--increment',
                    f'--increment-min={min_len}',
                    f'--increment-max={max_len}',
                    mask
                ]

        elif attack_type == 'Dictionary':
            wordlist = options.get('wordlist', '')
            if not wordlist or not os.path.exists(wordlist):
                messagebox.showerror("Error", "Please select a valid wordlist file.")
                return None
            return ['sudo', 'hashcat', '-m', '2500', hccapx_file, '-a', '0', wordlist]

        return None
