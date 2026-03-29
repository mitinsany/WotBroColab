from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModConfig:
    bot_token: str
    chat_id: str
    timeout_seconds: float = 3.0
    queue_size: int = 128

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)


def load_config_from_env(
    *,
    token_var: str = "WOT_TG_BOT_TOKEN",
    chat_var: str = "WOT_TG_CHAT_ID",
    timeout_var: str = "WOT_TG_TIMEOUT_SECONDS",
    queue_size_var: str = "WOT_TG_QUEUE_SIZE",
) -> ModConfig:
    token = (os.getenv(token_var) or "").strip()
    chat_id = (os.getenv(chat_var) or "").strip()

    timeout_raw = (os.getenv(timeout_var) or "3.0").strip()
    queue_raw = (os.getenv(queue_size_var) or "128").strip()

    timeout = _to_float(timeout_raw, fallback=3.0)
    queue_size = _to_int(queue_raw, fallback=128)
    if queue_size < 1:
        queue_size = 1

    return ModConfig(
        bot_token=token,
        chat_id=chat_id,
        timeout_seconds=timeout,
        queue_size=queue_size,
    )


def missing_config_reason(config: ModConfig) -> Optional[str]:
    missing = []
    if not config.bot_token:
        missing.append("WOT_TG_BOT_TOKEN")
    if not config.chat_id:
        missing.append("WOT_TG_CHAT_ID")
    if not missing:
        return None
    return "Missing required environment variables: {0}".format(", ".join(missing))


def _to_float(value: str, *, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    if parsed <= 0:
        return fallback
    return parsed


def _to_int(value: str, *, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
