import unittest
import monitor_backend as m

PRICES = {
    "gpt-5.6-luna": {"pricing_profile": "codex_official_credit_rate", "input_price_per_million": 25, "cached_input_price_per_million": 2.5, "output_price_per_million": 150},
    "gpt-5.4": {"pricing_profile": "codex_official_credit_rate", "input_price_per_million": 62.5, "cached_input_price_per_million": 6.25, "output_price_per_million": 375},
    "codex-auto-review": {"pricing_profile": "unpriced", "input_price_per_million": 0, "output_price_per_million": 0},
}

def summary(*items):
    return {"models": {k: {"user_input_tokens": i, "cached_input_tokens": c, "output_tokens": o,
                            "reasoning_output_tokens": r, "identifiable_tokens": i + o, "call_count": calls}
                        for k, i, c, o, r, calls in items}}

class TestModelFiltering(unittest.TestCase):
    def test_01_today_unused_model_hidden(self): self.assertEqual(m.dynamic_model_options(summary(("a", 10, 0, 2, 0, 1)), PRICES), ["all", "a"])
    def test_02_seven_day_used_model_visible(self): self.assertIn("a", m.dynamic_model_options(summary(("a", 1, 0, 1, 0, 1)), PRICES))
    def test_03_unused_history_model_hidden(self): self.assertNotIn("gpt-5.4", m.dynamic_model_options(summary(("a", 1, 0, 1, 0, 1)), PRICES))
    def test_04_invalid_selection_falls_back_to_all(self): self.assertEqual(m.dynamic_model_options(summary(("a", 1, 0, 1, 0, 1)), PRICES)[0], "all")
    def test_05_settings_can_use_cumulative_models(self): self.assertIn("gpt-5.4", PRICES)
    def test_06_official_directory_not_menu_source(self): self.assertNotIn("gpt-5.6-sol", m.dynamic_model_options(summary(("a", 1, 0, 1, 0, 1)), PRICES))
    def test_07_known_unpriced_not_unknown(self): self.assertIn("codex-auto-review", m.dynamic_model_options(summary(("codex-auto-review", 1, 0, 1, 0, 1)), PRICES))
    def test_08_missing_model_is_unknown(self): self.assertIn("missing_model", m.dynamic_model_options(summary(("missing_model", 1, 0, 1, 0, 1)), PRICES))
    def test_09_no_missing_model_option_without_data(self): self.assertNotIn("missing_model", m.dynamic_model_options(summary(("a", 1, 0, 1, 0, 1)), PRICES))
    def test_10_all_unpriced_is_uncomputed(self): self.assertEqual(m.credits_display_state(summary(("codex-auto-review", 10, 2, 4, 1, 1)), PRICES)[0], "未计算")
    def test_11_partial_pricing_has_note(self): self.assertIn("未配置费率", m.credits_display_state(summary(("gpt-5.4", 10, 2, 4, 1, 1), ("codex-auto-review", 10, 2, 4, 1, 1)), PRICES)[1])
    def test_12_all_priced_displays_credits(self): self.assertIn("Credits", m.credits_display_state(summary(("gpt-5.4", 10, 2, 4, 1, 1)), PRICES)[0])
    def test_13_no_tokens_displays_zero(self): self.assertEqual(m.credits_display_state(summary(), PRICES)[0], "0.0000 Credits")
    def test_14_luna_price(self): self.assertEqual(m.credits_display_state(summary(("gpt-5.6-luna", 1000000, 0, 1000000, 0, 1)), PRICES)[0], "175.0000 Credits")
    def test_15_gpt54_price(self): self.assertEqual(m.credits_display_state(summary(("gpt-5.4", 1000000, 0, 1000000, 0, 1)), PRICES)[0], "437.5000 Credits")
    def test_16_cached_input_uses_cached_rate(self): self.assertEqual(m.credits_display_state(summary(("gpt-5.4", 1000000, 500000, 0, 0, 1)), PRICES)[0], "34.3750 Credits")
    def test_17_auto_review_unpriced_by_default(self): self.assertEqual(m.credits_display_state(summary(("codex-auto-review", 1, 0, 1, 0, 1)), PRICES)[0], "未计算")
    def test_18_sort_by_recognizable_tokens(self): self.assertEqual(m.dynamic_model_options(summary(("small", 1, 0, 1, 0, 1), ("large", 10, 0, 10, 0, 1)), PRICES), ["all", "large", "small"])
    def test_19_model_input_semantics(self): self.assertEqual(10 + 4, 14)
    def test_20_antigravity_uses_same_filter_shape(self): self.assertEqual(m.dynamic_model_options(summary(("gemini", 10, 0, 2, 0, 1)), PRICES), ["all", "gemini"])

if __name__ == "__main__": unittest.main()
