import json
import re
import unittest
from datetime import datetime

import monitor_backend as m


class TestMidnightRecovery(unittest.TestCase):
    def test_01_utc_crosses_local_midnight(self):
        self.assertEqual(m.to_local_date("2026-07-17T16:10:00Z"), "2026-07-18")

    def test_02_one_jsonl_can_span_two_local_dates(self):
        events = ["2026-07-17T15:59:59Z", "2026-07-17T16:00:00Z"]
        self.assertEqual([m.to_local_date(x) for x in events], ["2026-07-17", "2026-07-18"])

    def test_03_new_date_directory_is_not_date_source(self):
        self.assertEqual(m.to_local_date("2026-07-17T16:10:00Z"), "2026-07-18")

    def test_04_new_rollout_is_not_excluded_by_old_cache(self):
        source = open("monitor_backend.py", encoding="utf-8").read()
        self.assertIn("glob.glob(os.path.expanduser(\"~/.codex/sessions/**/*.jsonl\")", source)
        self.assertIn("glob.glob(os.path.expanduser(\"~/.codex/archived_sessions/**/*.jsonl\")", source)

    def test_05_active_archived_dedup_uses_event_ids(self):
        source = open("monitor_backend.py", encoding="utf-8").read()
        self.assertIn('if event_id in seen_ids:', source)

    def test_06_empty_today_does_not_empty_all_time(self):
        dashboard = {"codex": {"today": {"models": {}}, "all_time": {"models": {"gpt-5.4": {}}}}}
        self.assertEqual(m.settings_model_ids("codex", {}, {"days": []}, dashboard),
                         ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"])

    def test_07_empty_today_keeps_settings_history_models(self):
        daily = {"days": [{"sources": {"codex": {"models": {"gpt-5.4": {}}}}}]}
        self.assertEqual(m.settings_model_ids("codex", {}, daily, {"codex": {"today": {"models": {}}}}),
                         ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"])

    def test_08_dashboard_scan_time_is_iso(self):
        value = datetime.now().astimezone().isoformat(timespec="seconds")
        self.assertRegex(value, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_09_swift_decode_defaults_optional_call_count(self):
        source = open("macos/AntigravityTokenMonitor/TokenCacheReader.swift", encoding="utf-8").read()
        self.assertIn("decodeIfPresent(Int.self, forKey: .callCount) ?? 0", source)

    def test_10_credits_are_equivalent_not_spent(self):
        source = open("macos/AntigravityTokenMonitor/MenuBarView.swift", encoding="utf-8").read()
        self.assertIn("Credits 等价用量", source)
        self.assertNotIn("Credits 消耗估算", source)

    def test_11_all_unpriced_is_uncomputed(self):
        text, _ = m.credits_display_state({"models": {"x": {"user_input_tokens": 10, "output_tokens": 2}}}, {})
        self.assertEqual(text, "未计算")

    def test_12_zero_tokens_is_zero_only_when_empty(self):
        text, _ = m.credits_display_state({"models": {}}, {})
        self.assertEqual(text, "0.0000 Credits")

    def test_13_unused_official_models_are_hidden(self):
        prices = {"gpt-5.5": {"provider": "OpenAI"}}
        self.assertEqual(m.settings_model_ids("codex", prices, {"days": []}, {}),
                         ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"])

    def test_14_settings_count_equals_actual_raw_ids(self):
        daily = {"days": [{"sources": {"codex": {"models": {"a": {}, "b": {}}}}}]}
        self.assertEqual(len(m.settings_model_ids("codex", {}, daily, {})), 4)

    def test_15_settings_has_bottom_padding(self):
        source = open("macos/AntigravityTokenMonitor/MenuBarView.swift", encoding="utf-8").read()
        self.assertRegex(source, r"padding\(\.bottom,\s*32\)")

    def test_16_antigravity_catalog_is_independent(self):
        daily = {"days": [{"sources": {"antigravity": {"models": {"gemini": {}}}, "codex": {"models": {"gpt": {}}}}}]}
        self.assertEqual(m.settings_model_ids("antigravity", {}, daily, {}),
                         ["claude-opus-4-6-thinking", "claude-sonnet-4-6", "gemini-3.5-flash", "gemini-3.1-pro", "gpt-oss-120b", "gemini"])


if __name__ == "__main__":
    unittest.main()
