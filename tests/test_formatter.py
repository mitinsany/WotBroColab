from __future__ import annotations

import unittest

from res_mods.mods.wot_telegram_notifier.constants import (
    BATTLE_END,
    BATTLE_START,
    PLAYER_LOGIN,
    PLAYER_LOGOUT,
)
from res_mods.mods.wot_telegram_notifier.formatter import MessageFormatter


class FormatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.formatter = MessageFormatter()
        self.base_payload = {
            "timestamp": "2026-03-18T14:20:00",
            "player": "TestPlayer",
            "meta": {},
        }

    def test_login_message(self) -> None:
        message = self.formatter.format(PLAYER_LOGIN, self.base_payload)
        self.assertIn("[WoT] login | TestPlayer | 2026-03-18 14:20:00", message)

    def test_logout_message(self) -> None:
        message = self.formatter.format(PLAYER_LOGOUT, self.base_payload)
        self.assertIn("[WoT] logout | TestPlayer | 2026-03-18 14:20:00", message)

    def test_battle_start_message(self) -> None:
        message = self.formatter.format(BATTLE_START, self.base_payload)
        self.assertIn("[WoT] battle_start | TestPlayer | 2026-03-18 14:20:00", message)

    def test_battle_end_with_details(self) -> None:
        payload = dict(self.base_payload)
        payload["meta"] = {"result": "victory", "duration": 420}
        message = self.formatter.format(BATTLE_END, payload)
        self.assertIn("[WoT] battle_end | TestPlayer | 2026-03-18 14:20:00", message)
        self.assertIn("result=victory", message)
        self.assertIn("duration=420s", message)


if __name__ == "__main__":
    unittest.main()
