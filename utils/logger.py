"""
utils/logger.py
Centralized logging setup for AirStrike.
All modules import and use this shared logger.
"""

import logging
from pathlib import Path

LOG_FILE = Path.home() / "airstrike.log"


def setup_logger():
    """
    Configure and return the AirStrike logger.
    Logs to both a file and the terminal console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("AirStrike")


# Shared logger instance used across all modules
logger = setup_logger()
