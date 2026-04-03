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


def load_config_from_ini(path: str) -> ModConfig:
    values = _read_ini_kv(path)
    token = (values.get("WOT_TG_BOT_TOKEN") or "").strip()
    chat_id = (values.get("WOT_TG_CHAT_ID") or "").strip()

    timeout_raw = (values.get("WOT_TG_TIMEOUT_SECONDS") or "3.0").strip()
    queue_raw = (values.get("WOT_TG_QUEUE_SIZE") or "128").strip()

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
    return "Missing required config keys: {0}".format(", ".join(missing))


def _read_ini_kv(path: str) -> dict:
    if not os.path.isfile(path):
        return {}

    parsed = {}
    with open(path, "r", encoding="utf-8") as stream:
        for raw in stream:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                parsed[key] = value
    return parsed


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
