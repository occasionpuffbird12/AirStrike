"""
ui/crack_tab.py
Password Cracking tab UI.
Allows cracking the captured WPA2 handshake using hashcat.
Talks to core/cracker.py for all backend operations.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from core.cracker import PasswordCracker, CHARSET_MAP


class CrackTab:
    """Builds and manages the Password Cracking tab."""

    def __init__(self, notebook, get_captured_file_callback, log_callback):
        """
        Args:
            notebook:                   The ttk.Notebook to attach this tab to
            get_captured_file_callback: Function that returns the captured .cap file path
            log_callback:               Function to write messages to the console
        """
        self.log               = log_callback
        self.get_captured_file = get_captured_file_callback
        self.cracker           = PasswordCracker()

        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Password Cracking")
        self._build_ui()

    def _build_ui(self):
        """Build all widgets for the Password Cracking tab."""
        # Handshake file path input
        ttk.Label(self.frame, text="Handshake File:").grid(
            row=0, column=0, padx=5, pady=5, sticky='w'
        )
        self.handshake_path = ttk.Entry(self.frame, width=50)
        self.handshake_path.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.frame, text="Browse",
                   command=self._browse_handshake).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(self.frame, text="Use Captured File",
                   command=self._use_captured_file).grid(row=0, column=3, padx=5, pady=5)

        # Attack type selector
        ttk.Label(self.frame, text="Attack Type:").grid(
            row=1, column=0, padx=5, pady=5, sticky='w'
        )
        self.attack_type = ttk.Combobox(
            self.frame, values=['Brute Force', 'Dictionary'], width=20
        )
        self.attack_type.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.attack_type.bind('<<ComboboxSelected>>', self._toggle_options)

        # Brute force options panel
        self.bf_frame = ttk.LabelFrame(self.frame, text="Brute Force Options")
        self.bf_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Label(self.bf_frame, text="Character Set:").grid(row=0, column=0, padx=5, pady=5)
        self.charset = ttk.Combobox(self.bf_frame, values=list(CHARSET_MAP.keys()), width=35)
        self.charset.set('Letters + Numbers')
        self.charset.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.bf_frame, text="Min Length:").grid(row=1, column=0, padx=5, pady=5)
        self.min_length = ttk.Entry(self.bf_frame, width=10)
        self.min_length.insert(0, "8")
        self.min_length.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        ttk.Label(self.bf_frame, text="Max Length:").grid(row=2, column=0, padx=5, pady=5)
        self.max_length = ttk.Entry(self.bf_frame, width=10)
        self.max_length.insert(0, "12")
        self.max_length.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # Dictionary options panel
        self.dict_frame = ttk.LabelFrame(self.frame, text="Dictionary Options")
        self.dict_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        ttk.Label(self.dict_frame, text="Wordlist File:").grid(row=0, column=0, padx=5, pady=5)
        self.wordlist_path = ttk.Entry(self.dict_frame, width=50)
        self.wordlist_path.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.dict_frame, text="Browse",
                   command=self._browse_wordlist).grid(row=0, column=2, padx=5, pady=5)
        self.dict_frame.grid_remove()  # Hidden until Dictionary selected

        # Start button
        ttk.Button(self.frame, text="Start Cracking",
                   command=self.start_cracking).grid(row=4, column=1, padx=5, pady=20)

        # Results display
        ttk.Label(self.frame, text="Cracking Results:").grid(
            row=5, column=0, padx=5, pady=5, sticky='w'
        )
        self.crack_results = scrolledtext.ScrolledText(self.frame, height=15, width=80)
        self.crack_results.grid(row=6, column=0, columnspan=4, padx=5, pady=5)

    def start_cracking(self):
        """Start the password cracking process."""
        self.crack_results.delete(1.0, tk.END)

        options = {
            'charset':  self.charset.get(),
            'min_len':  self.min_length.get().strip(),
            'max_len':  self.max_length.get().strip(),
            'wordlist': self.wordlist_path.get().strip()
        }

        self.cracker.start_cracking(
            handshake_file=self.handshake_path.get().strip(),
            attack_type=self.attack_type.get(),
            options=options,
            on_result=self._append_result,
            log_callback=self.log
        )

    def _append_result(self, text):
        """Append text to the cracking results panel."""
        self.crack_results.insert(tk.END, text)
        self.crack_results.see(tk.END)

    def _browse_handshake(self):
        """Open file dialog to select a .cap handshake file."""
        filename = filedialog.askopenfilename(
            filetypes=[("CAP files", "*.cap"), ("All files", "*.*")]
        )
        if filename:
            self.handshake_path.delete(0, tk.END)
            self.handshake_path.insert(0, filename)

    def _browse_wordlist(self):
        """Open file dialog to select a wordlist .txt file."""
        filename = filedialog.askopenfilename(
            filetypes=[("Wordlist files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wordlist_path.delete(0, tk.END)
            self.wordlist_path.insert(0, filename)

    def _use_captured_file(self):
        """Auto-fill the handshake path from the most recent capture."""
        filepath = self.get_captured_file()
        if filepath:
            self.handshake_path.delete(0, tk.END)
            self.handshake_path.insert(0, filepath)
            self.log(f"Loaded captured file: {filepath}")
        else:
            self.log("No captured file available yet.")

    def _toggle_options(self, event=None):
        """Show brute force or dictionary options based on selected attack type."""
        if self.attack_type.get() == 'Brute Force':
            self.dict_frame.grid_remove()
            self.bf_frame.grid()
        else:
            self.bf_frame.grid_remove()
            self.dict_frame.grid()
