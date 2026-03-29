from __future__ import annotations

import json
import logging
import threading
from abc import ABCMeta, abstractmethod
from queue import Full, Queue
from typing import Callable, Optional, Tuple
from urllib import error, parse, request

from .config import ModConfig
from .formatter import MessageFormatter
from .types import EventPayload

Transport = Callable[[str, str, float], None]


class Notifier(metaclass=ABCMeta):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def send(self, event_type: str, payload: EventPayload) -> None:
        raise NotImplementedError


class TelegramNotifier(Notifier):
    def __init__(
        self,
        *,
        config: ModConfig,
        logger: logging.Logger,
        formatter: Optional[MessageFormatter] = None,
        transport: Optional[Transport] = None,
    ) -> None:
        self._config = config
        self._logger = logger
        self._formatter = formatter or MessageFormatter()
        self._transport = transport or _send_message_http
        self._queue: Queue[Optional[Tuple[str, EventPayload]]] = Queue(maxsize=config.queue_size)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not self._config.enabled:
            self._logger.warning("Telegram notifier is disabled because configuration is incomplete.")
            return
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, name="wot-tg-notifier", daemon=True)
        self._thread.start()
        self._logger.info("Telegram notifier started.")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            try:
                self._queue.put_nowait(None)
            except Full:
                pass
            self._thread.join(timeout=1.0)
        self._logger.info("Telegram notifier stopped.")

    def send(self, event_type: str, payload: EventPayload) -> None:
        if not self._config.enabled:
            return
        item = (event_type, payload)
        try:
            self._queue.put_nowait(item)
        except Full:
            self._logger.warning("Telegram queue is full; dropping event: %s", event_type)

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            item = self._queue.get()
            if item is None:
                break

            event_type, payload = item
            message = self._formatter.format(event_type, payload)
            try:
                self._transport(
                    self._config.bot_token,
                    self._config.chat_id,
                    message,
                    self._config.timeout_seconds,
                )
                self._logger.info("Telegram message sent for event: %s", event_type)
            except Exception as exc:
                self._logger.error("Telegram send failed for %s: %s", event_type, exc)


def _send_message_http(bot_token: str, chat_id: str, message: str, timeout_seconds: float) -> None:
    url = "https://api.telegram.org/bot{0}/sendMessage".format(bot_token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True,
    }
    data = parse.urlencode(payload).encode("utf-8")
    req = request.Request(url=url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            body = response.read()
            _validate_telegram_response(body)
    except error.HTTPError as exc:
        body = exc.read()
        _validate_telegram_response(body, fallback=str(exc))
        raise


def _validate_telegram_response(body: bytes, fallback: str = "unexpected Telegram response") -> None:
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise RuntimeError(fallback)

    if not isinstance(payload, dict):
        raise RuntimeError(fallback)
    if payload.get("ok") is True:
        return

    description = payload.get("description") or fallback
    raise RuntimeError(str(description))
