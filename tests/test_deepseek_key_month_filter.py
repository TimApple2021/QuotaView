import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import deepseek_backend as backend


class DeepSeekKeyAndMonthTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.data, ignore_errors=True)

    def zip_for(self, name, rows):
        path = os.path.join(self.data, name)
        csv = "user_id,utc_date,model,api_key_name,api_key,type,price,amount\n" + "\n".join(rows) + "\n"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("amount.csv", csv)
        return path

    def row(self, date, name, key, tokens, model="deepseek-chat"):
        return f"u1,{date},{model},{name},{key},input_cache_miss_tokens,0.000002,{tokens}"

    def snapshot(self):
        return backend.get_deepseek_dashboard_snapshot(self.data)["usage"]

    def test_same_masked_key_names_merge_and_latest_name_is_displayed(self):
        z = self.zip_for("a.zip", [
            self.row("20310701", "Legacy Translation Worker", "sk-test1111", 10),
            self.row("20310702", "Primary Translation", "sk-test1111", 20),
        ])
        backend.import_deepseek_usage_zip(z, self.data)
        usage = self.snapshot()
        self.assertEqual(len(usage["keys"]), 1)
        self.assertEqual(usage["keys"][0]["api_key_name"], "Primary Translation")
        self.assertEqual(usage["total_tokens"], 30)

        history = json.load(open(os.path.join(self.data, "deepseek_usage_history.json")))
        self.assertIn("key_aliases", history)
        self.assertTrue(any("Legacy Translation Worker" in aliases for aliases in history["key_aliases"].values()))

    def test_different_keys_and_deleted_history_key_stay_separate(self):
        z = self.zip_for("keys.zip", [
            self.row("20310701", "Current", "sk-test1111", 10),
            self.row("20310701", "Deleted historical", "sk-demo2222", 20),
        ])
        backend.import_deepseek_usage_zip(z, self.data)
        self.assertEqual(len(self.snapshot()["keys"]), 2)

    def test_renamed_key_reimport_and_three_imports_do_not_double_count(self):
        old = self.zip_for("old.zip", [self.row("20310701", "Old", "sk-test1111", 10)])
        new = self.zip_for("new.zip", [self.row("20310701", "New", "sk-test1111", 10)])
        backend.import_deepseek_usage_zip(old, self.data)
        backend.import_deepseek_usage_zip(new, self.data)
        backend.import_deepseek_usage_zip(new, self.data)
        self.assertEqual(self.snapshot()["total_tokens"], 10)
        self.assertEqual(self.snapshot()["keys"][0]["api_key_name"], "New")

    def test_overlap_replaces_old_dates_and_adds_new_dates(self):
        first = self.zip_for("first.zip", [
            self.row("20310701", "K", "sk-test1111", 10),
            self.row("20310720", "K", "sk-test1111", 20),
        ])
        second = self.zip_for("second.zip", [
            self.row("20310701", "K", "sk-test1111", 11),
            self.row("20310720", "K", "sk-test1111", 21),
            self.row("20310721", "K", "sk-test1111", 30),
        ])
        backend.import_deepseek_usage_zip(first, self.data)
        backend.import_deepseek_usage_zip(second, self.data)
        usage = self.snapshot()
        self.assertEqual(usage["total_tokens"], 62)
        self.assertEqual(usage["coverage_start"], "2031-07-01")
        self.assertEqual(usage["coverage_end"], "2031-07-21")

    def test_months_descending_and_month_filter_keeps_balance_independent(self):
        z = self.zip_for("months.zip", [
            self.row("20310630", "K", "sk-test1111", 5),
            self.row("20310701", "K", "sk-test1111", 7),
            self.row("20310723", "K", "sk-test1111", 9),
        ])
        backend.import_deepseek_usage_zip(z, self.data)
        snapshot = backend.get_deepseek_dashboard_snapshot(self.data)
        self.assertEqual(snapshot["usage"]["available_months"], ["2031-07", "2031-06"])
        july = next(x for x in snapshot["usage"]["monthly_summaries"] if x["month"] == "2031-07")
        self.assertEqual(july["total_tokens"], 16)
        self.assertEqual(july["total_request_count"], 0)
        self.assertEqual(snapshot["usage"]["total_tokens"], 21)
        self.assertEqual(snapshot["balance"], snapshot["balance"])  # live node is not month-derived

    def test_monthly_summaries_sum_to_all_time_and_filter_models_and_keys(self):
        z = self.zip_for("models.zip", [
            self.row("20310601", "JuneKey", "sk-test1111", 5, "deepseek-chat"),
            self.row("20310701", "JulyKey", "sk-demo2222", 7, "deepseek-reasoner"),
        ])
        backend.import_deepseek_usage_zip(z, self.data)
        usage = backend.get_deepseek_dashboard_snapshot(self.data)["usage"]
        self.assertEqual(sum(x["total_tokens"] for x in usage["monthly_summaries"]), usage["total_tokens"])
        july = next(x for x in usage["monthly_summaries"] if x["month"] == "2031-07")
        self.assertEqual([x["model_id"] for x in july["models"]], ["deepseek-reasoner"])
        self.assertEqual(len(july["keys"]), 1)

    def test_every_month_uses_global_latest_key_name(self):
        z = self.zip_for("rename-months.zip", [
            self.row("20310109", "Legacy Translation Worker", "sk-test1111", 10),
            self.row("20310701", "Primary Translation", "sk-test1111", 20),
        ])
        backend.import_deepseek_usage_zip(z, self.data)
        usage = backend.get_deepseek_dashboard_snapshot(self.data)["usage"]
        for summary in usage["monthly_summaries"]:
            self.assertEqual(summary["keys"][0]["api_key_name"], "Primary Translation")

    def test_source_selection_is_not_used_for_menu_bar_aggregation(self):
        source = Path("macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text()
        update = source[source.index("func updateMenuBarText()") : source.index("private func formatMenuBarForSourceStats")]
        self.assertIn("switch selectedSource", update)
        self.assertNotIn("formatMenuBarForAll", source)
        self.assertNotIn("displayedSources {", update)

    def test_deepseek_menu_bar_range_is_based_on_daily_series(self):
        source = Path("macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text()
        self.assertIn("deepSeekRangeTokens(usg, days: 7)", source)
        self.assertIn("deepSeekRangeTokens(usg, days: 30)", source)
        self.assertIn('menuBarText = "—"', source)

    def test_deepseek_history_key_title_and_request_units_are_localized(self):
        source = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text()
        self.assertIn('按历史 API Key 统计', source)
        self.assertIn('Historical API Key Usage', source)
        self.assertIn('dataModel.fmt(usg?.totalRequestCount ?? 0)', source)
        self.assertIn('"\\(m.requestCount) requests"', source)
        self.assertNotIn('"API Requests"), value: "\\(dataModel.fmt(usg?.totalRequestCount ?? 0)) 次"', source)

    def test_english_deepseek_settings_button_and_coverage_are_localized(self):
        source = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text()
        self.assertIn('"Test & Refresh"', source)
        self.assertIn('"\\(usg?.coverageStart ?? "") to \\(usg?.coverageEnd ?? "")"', source)
        self.assertIn('"\\(usg?.coverageStart ?? "") 至 \\(usg?.coverageEnd ?? "")"', source)

    def test_english_pricing_text_and_stable_codex_columns(self):
        source = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text()
        self.assertIn("Standard context", source)
        self.assertIn("Long context", source)
        self.assertIn('Text("Cached").fixedSize', source)
        self.assertIn('Text("$\\(detail.standardCachedInputPrice', source)
        self.assertIn("private func priceColumn(label: String, value: Binding<Double>)", source)
        self.assertIn(".lineLimit(1)", source)
        self.assertNotIn('dataModel.tr("输入:", "Input:")', source)

    def test_legacy_dashboard_without_month_fields_is_compatible_in_source(self):
        text = Path("macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text()
        self.assertIn('availableMonths = (try? c.decode([String].self, forKey: .availableMonths)) ?? []', text)
        self.assertIn('monthlySummaries = (try? c.decode([DeepSeekMonthlySummary].self, forKey: .monthlySummaries)) ?? []', text)

    def test_schema_stays_one_and_raw_key_is_not_persisted(self):
        z = self.zip_for("privacy.zip", [self.row("20310701", "K", "sk-test1111", 10)])
        backend.import_deepseek_usage_zip(z, self.data)
        history = json.dumps(json.load(open(os.path.join(self.data, "deepseek_usage_history.json"))))
        dashboard = json.dumps(backend.get_deepseek_dashboard_snapshot(self.data))
        self.assertEqual(json.load(open(os.path.join(self.data, "deepseek_usage_history.json")))["schema_version"], 1)
        self.assertNotIn("sk-test1111", dashboard)
        self.assertIn("sk-t****1111", dashboard)
        self.assertIn("sk-t****1111", history)


if __name__ == "__main__":
    unittest.main()
