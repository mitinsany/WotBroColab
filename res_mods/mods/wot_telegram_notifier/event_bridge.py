from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from .constants import BATTLE_END, BATTLE_START, PLAYER_LOGIN, PLAYER_LOGOUT
from .notifier import Notifier
from .types import EventPayload


class EventBridge:
    def __init__(self, *, notifier: Notifier, logger: logging.Logger, player_name: Optional[str] = None) -> None:
        self._notifier = notifier
        self._logger = logger
        self._player_name = player_name or "unknown_player"

    def install_best_effort_hooks(self) -> None:
        hooked = 0
        hooked += _safe_call(self._hook_avatar_classic)
        hooked += _safe_call(self._hook_account_classic)
        if hooked == 0:
            self._logger.warning(
                "No WoT runtime hooks were installed automatically. "
                "Call EventBridge event methods from your client hooks."
            )
        else:
            self._logger.info("Installed %s WoT hook set(s).", hooked)

    def on_player_login(self, *, player_name: Optional[str] = None) -> None:
        self._emit(PLAYER_LOGIN, player_name=player_name)

    def on_player_logout(self, *, player_name: Optional[str] = None) -> None:
        self._emit(PLAYER_LOGOUT, player_name=player_name)

    def on_battle_start(self, *, player_name: Optional[str] = None, meta: Optional[dict] = None) -> None:
        self._emit(BATTLE_START, player_name=player_name, meta=meta)

    def on_battle_end(self, *, player_name: Optional[str] = None, meta: Optional[dict] = None) -> None:
        self._emit(BATTLE_END, player_name=player_name, meta=meta)

    def _emit(self, event_type: str, *, player_name: Optional[str] = None, meta: Optional[dict] = None) -> None:
        payload: EventPayload = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "player": player_name or self._player_name,
            "meta": meta or {},
        }
        self._logger.info("Captured game event: %s", event_type)
        self._notifier.send(event_type, payload)

    def _hook_account_classic(self) -> int:
        try:
            import Account
        except Exception:
            return 0

        account_cls = getattr(Account, "Account", None)
        if account_cls is None:
            return 0

        _wrap_method(
            account_cls,
            "_doCmdLogin",
            after=lambda _self, _args, _kwargs, _result: self.on_player_login(),
            logger=self._logger,
        )
        _wrap_method(
            account_cls,
            "onBecomeNonPlayer",
            after=lambda _self, _args, _kwargs, _result: self.on_player_logout(),
            logger=self._logger,
        )
        return 1

    def _hook_avatar_classic(self) -> int:
        try:
            import Avatar
        except Exception:
            return 0

        avatar_cls = getattr(Avatar, "PlayerAvatar", None)
        if avatar_cls is None:
            return 0

        _wrap_method(
            avatar_cls,
            "_PlayerAvatar__startGUI",
            after=lambda _self, _args, _kwargs, _result: self.on_battle_start(),
            logger=self._logger,
        )
        _wrap_method(
            avatar_cls,
            "_PlayerAvatar__destroyGUI",
            after=lambda _self, _args, _kwargs, _result: self.on_battle_end(),
            logger=self._logger,
        )
        return 1


def _safe_call(fn: Callable[[], int]) -> int:
    try:
        return fn()
    except Exception:
        return 0


def _wrap_method(target_cls: Any, method_name: str, *, after: Callable[[Any, tuple, dict, Any], None], logger: logging.Logger) -> None:
    original = getattr(target_cls, method_name, None)
    if original is None:
        return
    if getattr(original, "__wot_tg_wrapped__", False):
        return

    def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = original(self, *args, **kwargs)
        try:
            after(self, args, kwargs, result)
        except Exception as exc:
            logger.warning("Hook callback failed for %s.%s: %s", target_cls.__name__, method_name, exc)
        return result

    setattr(wrapped, "__wot_tg_wrapped__", True)
    setattr(target_cls, method_name, wrapped)
