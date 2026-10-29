import logging
import os
import sys


def setup_logger(
    name: str,
    log_path: str | None = None,
    level: str = "DEBUG",
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(getattr(logging, level))

    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )

    if log_path:
        os.makedirs(log_path, exist_ok=True)
        log_file = os.path.join(log_path, "application.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_path == "" or log_path is None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
