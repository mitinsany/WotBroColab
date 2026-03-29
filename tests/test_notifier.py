from __future__ import annotations

import logging
import unittest

from res_mods.mods.wot_telegram_notifier.config import ModConfig
from res_mods.mods.wot_telegram_notifier.constants import PLAYER_LOGIN
from res_mods.mods.wot_telegram_notifier.notifier import TelegramNotifier


class NotifierTests(unittest.TestCase):
    def test_send_failure_is_swallowed(self) -> None:
        seen = []

        def failing_transport(_bot_token: str, _chat_id: str, _text: str, _timeout: float) -> None:
            seen.append("called")
            raise RuntimeError("network down")

        logger = logging.getLogger("test.notifier")
        logger.handlers.clear()
        logger.addHandler(logging.NullHandler())

        notifier = TelegramNotifier(
            config=ModConfig(bot_token="token", chat_id="chat", timeout_seconds=0.1, queue_size=8),
            logger=logger,
            transport=failing_transport,
        )

        notifier.start()
        notifier.send(
            PLAYER_LOGIN,
            {"timestamp": "2026-03-18T14:20:00", "player": "tester", "meta": {}},
        )
        notifier.stop()

        self.assertTrue(seen)


if __name__ == "__main__":
    unittest.main()
