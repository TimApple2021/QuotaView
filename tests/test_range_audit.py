import json
import re
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
MODEL = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
VIEW = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
CLI = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")


class RangeAuditTests(unittest.TestCase):
    def test_backend_uses_local_natural_day_cutoffs(self):
        self.assertIn("today_str   = datetime.now().strftime(\"%Y-%m-%d\")", BACKEND)
        self.assertIn("today_dt    = date_cls.today()", BACKEND)
        self.assertIn("timedelta(days=6)", BACKEND)
        self.assertIn("timedelta(days=29)", BACKEND)

    def test_range_windows_are_inclusive_today_plus_previous_days(self):
        today = date(2024, 2, 29)
        self.assertEqual(today - timedelta(days=6), date(2024, 2, 23))
        self.assertEqual(today - timedelta(days=29), date(2024, 1, 31))
        year_end = date(2023, 12, 31)
        self.assertEqual(year_end - timedelta(days=29), date(2023, 12, 2))

    def test_dashboard_ranges_are_sum_by_same_source_and_date_set(self):
        self.assertIn('"today":    _sum_range_v4(today_str, "antigravity")', BACKEND)
        self.assertIn('"last_7":   _sum_range_v4(day7_cutoff, "antigravity")', BACKEND)
        self.assertIn('"last_30":  _sum_range_v4(day30_cutoff, "antigravity")', BACKEND)
        self.assertIn('"all_time": _sum_range_v4(None, "antigravity")', BACKEND)
        self.assertIn('"today":    _sum_range_v4(today_str, "codex")', BACKEND)
        self.assertIn('"last_7":   _sum_range_v4(day7_cutoff, "codex")', BACKEND)
        self.assertIn('"last_30":  _sum_range_v4(day30_cutoff, "codex")', BACKEND)
        self.assertIn('"all_time": _sum_range_v4(None, "codex")', BACKEND)

    def test_missing_days_are_zero_filled(self):
        self.assertIn("Generate continuous daily entries with 0-fill", BACKEND)
        self.assertIn("src_day = day_data.get(src_name, {", BACKEND)

    def test_cost_and_tokens_are_aggregated_from_same_model_rows(self):
        block = BACKEND[BACKEND.index("def _sum_range_v4"):BACKEND.index("# ── Continuous series helpers")]
        self.assertIn('ident += src_data["identifiable_tokens"]', block)
        self.assertIn('total_cost_dec = Decimal("0.0")', block)
        self.assertIn('m_sum["estimated_cost"]', block)

    def test_cli_exposes_all_four_ranges_without_schema_change(self):
        self.assertIn('choices=["today", "7d", "30d", "all"]', CLI)
        self.assertIn('return {"today": "today", "7d": "last_7", "30d": "last_30", "all": "all_time"}', CLI)
        self.assertIn('SCHEMA_VERSION = 1', CLI)

    def test_menu_bar_has_explicit_30_day_mapping(self):
        self.assertIn('case days30Total = "30 日可识别"', MODEL)
        self.assertIn('case .days30Total: menuBarText = fmt(ss.last30.identifiableTokens)', MODEL)
        self.assertNotIn('case .days30Total: menuBarText = fmt(ss.today.identifiableTokens)', MODEL)

    def test_menu_bar_cost_is_cumulative_and_source_specific(self):
        self.assertIn('case .allCost:', MODEL)
        self.assertIn('ss.allTime.estimatedCost', MODEL)
        self.assertIn('dashboard.sources[selectedSource.jsonKey]', MODEL)

    def test_menu_bar_cost_uses_dollar_symbol_for_both_sources(self):
        self.assertIn('formatMenuBarForSourceStats', MODEL)
        self.assertIn('menuBarText = "\\(currencySymbol)\\(String(format: "%.2f", ss.allTime.estimatedCost))"', MODEL)

    def test_other_menu_bar_modes_remain_token_based(self):
        self.assertIn('case .iconOnly:    menuBarText = ""', MODEL)
        self.assertIn('case .todayTotal:  menuBarText = fmt(ss.today.identifiableTokens)', MODEL)
        self.assertIn('case .days7Total:  menuBarText = fmt(ss.last7.identifiableTokens)', MODEL)
        self.assertIn('case .days30Total: menuBarText = fmt(ss.last30.identifiableTokens)', MODEL)
        self.assertIn('case .allTotal:    menuBarText = fmt(ss.allTime.identifiableTokens)', MODEL)


    def test_menu_bar_cost_keeps_two_decimal_format(self):
        self.assertIn('String(format: "%.2f", ss.allTime.estimatedCost)', MODEL)

    def test_main_range_labels_and_hint_are_clear(self):
        self.assertIn('case days7   = "近 7 天"', MODEL)
        self.assertIn('case days30  = "近 30 天"', MODEL)
        self.assertIn('case allTime = "本地累计"', MODEL)
        self.assertIn('settingRow(dataModel.tr("主页面默认范围", "Main Page Default Range"))', VIEW)
        self.assertIn('dataModel.timeRangeLabel(dataModel.selectedRange)', VIEW)

    def test_legacy_range_values_migrate(self):
        self.assertIn('"7 天": .days7', MODEL)
        self.assertIn('"30 天": .days30', MODEL)
        self.assertIn('"累计": .allTime', MODEL)

    def test_protected_features_remain_present(self):
        self.assertIn('quota_status', BACKEND)
        self.assertIn('reset_entitlements', BACKEND)
        self.assertIn('official_live', BACKEND)
        self.assertIn('pricing_tier', BACKEND)


if __name__ == "__main__":
    unittest.main()
