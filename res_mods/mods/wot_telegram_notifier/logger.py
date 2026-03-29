from __future__ import annotations

import logging
import os


def build_logger() -> logging.Logger:
    logger = logging.getLogger("wot.telegram.notifier")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    logs_dir = os.path.join(os.getcwd(), "logs")
    try:
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, "wot_telegram_notifier.log"),
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        logger.warning("Failed to initialize file logger; using stream only.")

    return logger
