from __future__ import annotations

import os
import tempfile
import unittest

from res_mods.mods.wot_telegram_notifier.config import load_config_from_ini, missing_config_reason


class ConfigTests(unittest.TestCase):
    def test_missing_ini_is_reported(self) -> None:
        config = load_config_from_ini("not_exists.ini")
        reason = missing_config_reason(config)
        self.assertFalse(config.enabled)
        self.assertIsNotNone(reason)
        self.assertIn("WOT_TG_BOT_TOKEN", reason)
        self.assertIn("WOT_TG_CHAT_ID", reason)

    def test_valid_ini_enables_notifier(self) -> None:
        fd, path = tempfile.mkstemp(prefix="wot_bro_colab_", suffix=".ini")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as stream:
                stream.write("WOT_TG_BOT_TOKEN=token\n")
                stream.write("WOT_TG_CHAT_ID=-100123\n")
            config = load_config_from_ini(path)
            reason = missing_config_reason(config)
            self.assertTrue(config.enabled)
            self.assertIsNone(reason)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
