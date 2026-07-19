import json
import unittest
from decimal import Decimal

import monitor_backend as m


class TestPricingTierAndQuotaBehavior(unittest.TestCase):
    def test_standard_prices_are_the_default(self):
        settings = m.load_settings()
        gem = settings["model_prices"]["gemini-3-flash-a"]
        self.assertEqual(settings.get("pricing_tier"), "standard")
        self.assertEqual((gem["input_price_per_million"], gem["cached_input_price_per_million"], gem["output_price_per_million"]), (1.5, 0.15, 9.0))

    def test_priority_prices_are_supported_without_mutating_user_override(self):
        original = m.SETTINGS_FILE
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            m.SETTINGS_FILE = os.path.join(td, "settings.json")
            with open(m.SETTINGS_FILE, "w") as f:
                json.dump({"pricing_tier": "priority", "model_prices": {"gemini-3-flash-a": {"user_overridden": False}}}, f)
            settings = m.load_settings()
            gem = settings["model_prices"]["gemini-3-flash-a"]
            self.assertEqual((gem["input_price_per_million"], gem["cached_input_price_per_million"], gem["output_price_per_million"]), (2.7, 0.27, 16.2))
            with open(m.SETTINGS_FILE, "w") as f:
                json.dump({"pricing_tier": "priority", "model_prices": {"gemini-3-flash-a": {"user_overridden": True, "input_price_per_million": 7, "output_price_per_million": 8}}}, f)
            settings = m.load_settings()
            gem = settings["model_prices"]["gemini-3-flash-a"]
            self.assertEqual((gem["input_price_per_million"], gem["output_price_per_million"]), (7, 8))
        m.SETTINGS_FILE = original

    def test_cached_tokens_are_not_double_counted_in_cost(self):
        summary = {"models": {"gemini-3-flash-a": {"user_input_tokens": 1_000_000, "cached_input_tokens": 500_000, "output_tokens": 1_000_000}}}
        text, _ = m.credits_display_state(summary, {"gemini-3-flash-a": {"input_price_per_million": 1.5, "cached_input_price_per_million": 0.15, "output_price_per_million": 9.0}})
        self.assertEqual(text, "9.8250 Credits")

    def test_quota_status_never_uses_historical_log_as_live(self):
        status = m.get_quota_status({}, [])
        self.assertNotEqual(status["codex"]["status"], "historical_log")
        self.assertTrue(all(item.get("confidence") == "official_live" for item in status["codex"]["items"]))

    def test_unavailable_quota_has_placeholder_and_no_items(self):
        status = m.read_codex_accessibility_quota()
        if status["status"] != "official_live":
            self.assertEqual(status["message"], "暂时无法读取当前官方额度")
            self.assertEqual(status["items"], [])


if __name__ == "__main__":
    unittest.main()
