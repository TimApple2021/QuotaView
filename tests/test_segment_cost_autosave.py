import unittest
from pathlib import Path

import monitor_backend as backend
from cli import quotaview_cli as cli


MENU = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
MODEL = Path("macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
CACHE = Path("macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text(encoding="utf-8")


class TestSegmentCostAutosave(unittest.TestCase):
    def prices(self):
        return {
            "gemini-3-flash-a": {"input_price_per_million": 1.5, "cached_input_price_per_million": .15, "output_price_per_million": 9, "pricing_profile": "api_standard_equivalent"},
            "gemini-3.1-pro": {"input_price_per_million": 2, "cached_input_price_per_million": .2, "output_price_per_million": 12, "threshold_tokens": 200000, "standard": {"input": 2, "cached": .2, "output": 12}, "long_context": {"input": 4, "cached": .4, "output": 18}, "pricing_profile": "api_standard_equivalent_tiered"},
            "claude-sonnet-4-6": {"input_price_per_million": 3, "output_price_per_million": 15, "pricing_profile": "api_standard_equivalent"},
            "claude-opus-4-6-thinking": {"input_price_per_million": 5, "output_price_per_million": 25, "pricing_profile": "api_standard_equivalent"},
            "gpt-oss-120b": {"input_price_per_million": 0, "output_price_per_million": 0, "pricing_profile": "unpriced"},
        }

    def test_segment_track_has_light_system_background(self):
        self.assertIn("segmentTrackBackground = Color(nsColor: light ? .controlBackgroundColor", MENU)

    def test_segment_track_is_not_gray(self):
        self.assertNotIn("Color.gray", MENU)
        self.assertNotIn("segmentTrackBackground = Color.black", MENU)

    def test_selected_segment_is_solid_accent(self):
        self.assertIn("selectedSegmentBackground", MENU)
        self.assertIn(".controlAccentColor).opacity(0.18)", MENU)
        self.assertIn(".fill(isSelected ? palette.selectedSegmentBackground", MENU)

    def test_unselected_segment_is_transparent(self):
        self.assertIn("Color.clear", MENU)
        self.assertIn("inactiveSegmentText", MENU)

    def test_dark_segment_branch_exists(self):
        self.assertIn(".controlBackgroundColor", MENU)
        self.assertIn(".selectedControlColor", MENU)

    def test_gemini_default_alias_is_priced(self):
        self.assertEqual(backend.normalize_antigravity_model("gemini-default"), "gemini-3-flash-a")
        self.assertGreater(float(backend.cost_for_call("gemini-default", 1_000_000, 0, 0, self.prices())), 0)

    def test_flash_cost_is_positive(self):
        self.assertGreater(float(backend.cost_for_call("gemini-3-flash-a", 1_000_000, 0, 1_000_000, self.prices())), 0)

    def test_gemini_pro_standard_tier(self):
        cost = backend.cost_for_call("gemini-3.1-pro", 200_000, 0, 100_000, self.prices())
        self.assertAlmostEqual(float(cost), 1.6, places=6)

    def test_gemini_pro_long_context_tier(self):
        cost = backend.cost_for_call("gemini-3.1-pro", 200_001, 0, 100_000, self.prices())
        self.assertAlmostEqual(float(cost), 2.600004, places=6)

    def test_gemini_pro_tier_uses_single_request_input(self):
        self.assertEqual(backend.pricing_rates_for_model("gemini-3.1-pro", 200_000, self.prices()), (2.0, .2, 12.0))
        self.assertEqual(backend.pricing_rates_for_model("gemini-3.1-pro", 200_001, self.prices()), (4.0, .4, 18.0))

    def test_claude_sonnet_priced(self):
        self.assertTrue(backend.is_priced_model("claude-sonnet-4-6", self.prices()))

    def test_claude_opus_priced(self):
        self.assertTrue(backend.is_priced_model("claude-opus-4-6-thinking", self.prices()))

    def test_unpriced_does_not_zero_priced_model(self):
        summary = {"models": {"gemini-3-flash-a": {"input_tokens": 1_000_000, "output_tokens": 0, "identifiable_tokens": 1_000_000}, "gpt-oss-120b": {"input_tokens": 1_000_000, "output_tokens": 0, "identifiable_tokens": 1_000_000}}}
        text, _ = backend.credits_display_state(summary, self.prices())
        self.assertNotEqual(text, "未计算")

    def test_oss_stays_unpriced(self):
        self.assertFalse(backend.is_priced_model("gpt-oss-120b", self.prices()))

    def test_resolved_cli_reports_actual_model(self):
        dashboard = {"sources": {"antigravity": {"today": {"models": {"gemini-default": {"user_input_tokens": 10, "output_tokens": 2, "estimated_cost": 0.0001}}}}}}
        rows = cli.resolved_pricing_data("antigravity", dashboard, {"model_prices": {"gemini-3-flash-a": self.prices()["gemini-3-flash-a"]}})
        self.assertEqual(rows[0]["raw_model_id"], "gemini-default")
        self.assertEqual(rows[0]["normalized_model_id"], "gemini-3-flash-a")

    def test_picker_save_button_removed(self):
        self.assertNotIn('Button("保存")', MENU)

    def test_picker_changes_persist(self):
        self.assertIn('forKey: "menuBarDisplay3"', MODEL)
        self.assertIn('forKey: "defaultRange"', MODEL)
        self.assertIn('forKey: "refreshInterval"', MODEL)

    def test_theme_changes_persist_and_apply(self):
        self.assertIn('case theme', MODEL)
        self.assertIn("applyAppearance()", MODEL)

    def test_refresh_change_rebuilds_timer(self):
        self.assertIn("setupTimer(); persistSettingsIfReady()", MODEL)

    def test_price_edit_saves_on_submit(self):
        self.assertIn("updateModelPrice", MENU)
        self.assertEqual(MENU.count(".onSubmit { dataModel.saveSettingsFile() }"), 3)

    def test_save_failure_is_visible(self):
        self.assertIn("settingsError", MODEL)
        self.assertIn("设置保存失败", MENU)

    def test_atomic_settings_write_remains(self):
        self.assertIn("replaceItemAt", MODEL)
        self.assertIn("appendingPathExtension(\"tmp\")", MODEL)

    def test_token_and_quota_models_unchanged(self):
        self.assertIn("quotaStatus", CACHE)
        self.assertIn("resetEntitlements", CACHE)
        self.assertIn("identifiableTokens", CACHE)

    def test_cli_schema_unchanged(self):
        self.assertEqual(cli.SCHEMA_VERSION, 1)


if __name__ == "__main__":
    unittest.main()
