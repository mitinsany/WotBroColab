from __future__ import annotations

from typing import Optional, Tuple

from .config import load_config_from_env, missing_config_reason
from .event_bridge import EventBridge
from .logger import build_logger
from .notifier import TelegramNotifier


def bootstrap() -> Tuple[Optional[TelegramNotifier], Optional[EventBridge]]:
    logger = build_logger()
    config = load_config_from_env()

    reason = missing_config_reason(config)
    if reason:
        logger.warning("%s. Mod will capture events but skip Telegram delivery.", reason)

    notifier = TelegramNotifier(config=config, logger=logger)
    bridge = EventBridge(notifier=notifier, logger=logger)

    notifier.start()
    bridge.install_best_effort_hooks()
    logger.info("WoT Telegram notifier mod initialized.")
    return notifier, bridge
