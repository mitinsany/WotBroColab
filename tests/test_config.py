from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from res_mods.mods.wot_telegram_notifier.config import load_config_from_env, missing_config_reason


class ConfigTests(unittest.TestCase):
    def test_missing_env_is_reported(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = load_config_from_env()
            reason = missing_config_reason(config)
            self.assertFalse(config.enabled)
            self.assertIsNotNone(reason)
            self.assertIn("WOT_TG_BOT_TOKEN", reason)
            self.assertIn("WOT_TG_CHAT_ID", reason)

    def test_valid_env_enables_notifier(self) -> None:
        with patch.dict(
            os.environ,
            {"WOT_TG_BOT_TOKEN": "token", "WOT_TG_CHAT_ID": "-100123"},
            clear=True,
        ):
            config = load_config_from_env()
            reason = missing_config_reason(config)
            self.assertTrue(config.enabled)
            self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
