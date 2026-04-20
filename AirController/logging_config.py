import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    logger = logging.getLogger()
    logger.setLevel(level)

    logger.handlers.clear()

    # File handler (always)
    log_file = __create_log_file()
    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (only for verbose mode)
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)


def __create_log_file():
    log_dir = os.path.expanduser("~/.local/share/aircontroller/")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "aircontroller.log")
