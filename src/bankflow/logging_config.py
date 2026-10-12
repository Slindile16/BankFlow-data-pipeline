"""Shared logging setup for BankFlow command-line entry points."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_file=None):
    """Log INFO and higher messages to the console and a rotating log file.

    By default, logs are written to ``logs/bankflow.log`` in the project root.
    Existing application logging configuration is left in place.
    """
    if logging.getLogger().handlers:
        return

    if log_file is None:
        project_root = Path(__file__).resolve().parents[2]
        log_file = project_root / "logs" / "bankflow.log"
    else:
        log_file = Path(log_file)

    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                log_file,
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            ),
        ],
    )
