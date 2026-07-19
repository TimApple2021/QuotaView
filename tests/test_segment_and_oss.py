import json
import unittest
from pathlib import Path

from cli import quotaview_cli as cli


MENU = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
BACKEND = Path("monitor_backend.py").read_text(encoding="utf-8")


class TestSegmentAndOSS(unittest.TestCase):
    def test_light_segment_track_is_not_dark_gray(self):
        self.assertNotIn("segmentTrackBackground = Color.black", MENU)
        self.assertIn("segmentTrackBackground = Color(nsColor: light ? .controlBackgroundColor", MENU)

    def test_light_segment_uses_light_track(self):
        self.assertIn("segmentTrackBackground", MENU)
        self.assertIn(".controlBackgroundColor", MENU)

    def test_selected_segment_has_independent_background(self):
        self.assertIn("selectedSegmentBackground", MENU)
        self.assertIn(".fill(isSelected ? palette.selectedSegmentBackground", MENU)

    def test_selected_segment_has_border(self):
        self.assertIn("selectedSegmentBorder", MENU)
        self.assertIn(".stroke(isSelected ? palette.selectedSegmentBorder", MENU)

    def test_selected_segment_has_light_shadow(self):
        self.assertIn("segmentShadow", MENU)
        self.assertIn("radius: 1.5", MENU)
        self.assertIn("y: 1", MENU)

    def test_inactive_segment_uses_secondary_text(self):
        self.assertIn("palette.inactiveSegmentText", MENU)

    def test_dark_segment_style_remains(self):
        self.assertIn(".controlAccentColor).opacity(0.18)", MENU)
        self.assertIn("light ? .controlBackgroundColor : .underPageBackgroundColor", MENU)

    def test_segment_switch_logic_unchanged(self):
        self.assertIn("dataModel.selectedSource = source", MENU)
        self.assertIn('sourceSegment(label: "Antigravity", source: .antigravity)', MENU)
        self.assertIn('sourceSegment(label: "Codex", source: .codex)', MENU)

    def test_oss_remains_unpriced(self):
        self.assertIn('"gpt-oss-120b"', BACKEND)
        self.assertIn('"pricing_profile": "unpriced"', BACKEND)

    def test_oss_has_no_price_inputs(self):
        branch = MENU[MENU.index('if detail.pricingProfile == "unpriced"'):MENU.index('} else if key == "gemini-3.1-pro"')]
        self.assertNotIn("TextField", branch)

    def test_oss_open_weight_copy(self):
        self.assertIn("开放权重｜无统一 API 单价", MENU)

    def test_oss_cost_copy(self):
        self.assertIn("运行成本取决于托管平台或本地算力", MENU)

    def test_oss_cli_semantics(self):
        settings = {"model_prices": {"gpt-oss-120b": {"display_name": "GPT-OSS 120B", "pricing_profile": "unpriced"}}}
        rows = cli.prices_data("antigravity", settings, False)
        oss = next(row for row in rows if row["raw_model_id"] == "gpt-oss-120b")
        self.assertTrue(oss["unpriced"])
        self.assertEqual(oss["unpriced_status"], "open_weight_no_unified_api_price")
        self.assertNotIn("input_price_per_million", oss)
        self.assertNotIn("output_price_per_million", oss)

    def test_cli_schema_version_unchanged(self):
        self.assertEqual(cli.SCHEMA_VERSION, 1)

    def test_backend_unpriced_token_fields_remain(self):
        self.assertIn("unpriced_tokens", BACKEND)


if __name__ == "__main__":
    unittest.main()
