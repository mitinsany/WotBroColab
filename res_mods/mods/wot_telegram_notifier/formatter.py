from __future__ import annotations

from datetime import datetime
from typing import Optional

from .constants import EVENT_LABELS
from .types import EventPayload


class MessageFormatter:
    def format(self, event_type: str, payload: EventPayload) -> str:
        label = EVENT_LABELS.get(event_type, event_type.lower())
        player = payload.get("player") or "unknown_player"
        timestamp = payload.get("timestamp")
        local_time = _format_time(timestamp)

        message = "[WoT] {0} | {1} | {2}".format(label, player, local_time)
        if label == "battle_end":
            details = _battle_end_details(payload)
            if details:
                message = "{0} | {1}".format(message, details)
        return message


def _format_time(timestamp: object) -> str:
    if not timestamp:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(timestamp, datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    try:
        parsed = datetime.fromisoformat(str(timestamp))
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return str(timestamp)


def _battle_end_details(payload: EventPayload) -> Optional[str]:
    meta = payload.get("meta") or {}
    if not isinstance(meta, dict):
        return None

    result = meta.get("result")
    duration = meta.get("duration")
    detail_parts = []
    if result:
        detail_parts.append("result={0}".format(result))
    if duration is not None:
        detail_parts.append("duration={0}s".format(duration))

    if not detail_parts:
        return None
    return ", ".join(detail_parts)
