import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from cli import quotaview_cli as cli


def dashboard():
    row = {"user_input_tokens": 10, "output_tokens": 5, "identifiable_tokens": 15, "estimated_cost": 1.25, "models": {}}
    return {
        "last_scan_time": "2026-07-19T10:00:00+08:00",
        "sources": {"antigravity": {"today": row, "last_7": row, "last_30": row, "all_time": row}, "codex": {"today": row, "last_7": row, "last_30": row, "all_time": row}},
        "quota_status": {
            "antigravity": {"status": "official_live", "items": [{"name": "Gemini 周额度", "used_percent": 20, "reset_time": "2026-07-20T00:00:00Z", "confidence": "official_live", "percent_semantics": "remaining", "observed_at": "2026-07-19T10:00:00Z", "source_path": "rpc", "original_field_name": "bucket.remaining.remainingFraction"}]},
            "codex": {"status": "official_live", "items": [], "reset_entitlements": {"status": "official_live", "available_count": 0, "count_semantics": "official", "items": [], "source_path": "codex_app_server_rpc", "observed_at": "2026-07-19T10:00:00Z"}},
        },
    }


class TestQuotaViewCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = cli.RUNTIME_DIR
        cli.RUNTIME_DIR = Path(self.tmp.name)
        (cli.RUNTIME_DIR / "dashboard.json").write_text(json.dumps(dashboard()), encoding="utf-8")
        (cli.RUNTIME_DIR / "settings.json").write_text(json.dumps({"model_prices": {
            "gemini-3.1-pro": {"display_name": "Gemini 3.1 Pro", "threshold_tokens": 200000, "standard": {"input": 2, "cached": .2, "output": 12}, "long_context": {"input": 4, "cached": .4, "output": 18}},
            "gpt-oss-120b": {"display_name": "GPT-OSS 120B", "pricing_profile": "unpriced"},
            "gpt-5.6-luna": {"display_name": "GPT-5.6 Luna", "input_price_per_million": 1, "output_price_per_million": 6},
            "gpt-5.4": {"display_name": "GPT-5.4", "input_price_per_million": 2.5, "output_price_per_million": 15},
        }}), encoding="utf-8")

    def tearDown(self):
        cli.RUNTIME_DIR = self.old
        self.tmp.cleanup()

    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(list(args))
        return code, out.getvalue()

    def test_status_text_output(self): self.assertEqual(self.run_main("status")[0], 0)
    def test_status_json_output(self): self.assertEqual(json.loads(self.run_main("status", "--json")[1])["schema_version"], 1)
    def test_usage_today(self): self.assertEqual(self.run_main("usage", "all", "--range", "today")[0], 0)
    def test_usage_7d(self): self.assertEqual(self.run_main("usage", "all", "--range", "7d")[0], 0)
    def test_usage_30d(self): self.assertEqual(self.run_main("usage", "all", "--range", "30d")[0], 0)
    def test_usage_all(self): self.assertEqual(self.run_main("usage", "all", "--range", "all")[0], 0)
    def test_usage_antigravity_filter(self): self.assertEqual(self.run_main("usage", "antigravity")[0], 0)
    def test_usage_codex_filter(self): self.assertEqual(self.run_main("usage", "codex")[0], 0)
    def test_quota_fault_isolated(self):
        d = dashboard(); del d["quota_status"]["codex"]; (cli.RUNTIME_DIR / "dashboard.json").write_text(json.dumps(d), encoding="utf-8")
        result = cli.quota_data("all", d); self.assertEqual(result["antigravity"]["status"], "official_live"); self.assertEqual(result["codex"]["status"], "unavailable")
    def test_resets_zero_count(self): self.assertEqual(cli.reset_data(dashboard())["available_count"], 0)
    def test_resets_items_missing(self):
        d = dashboard(); d["quota_status"]["codex"]["reset_entitlements"].pop("items"); self.assertEqual(cli.reset_data(d)["items"], [])
    def test_resets_corrupt_item_ignored(self):
        d = dashboard(); d["quota_status"]["codex"]["reset_entitlements"]["items"] = [None, {"status": "used"}]; self.assertEqual(cli.reset_data(d)["items"], [])
    def test_resets_only_available(self):
        d = dashboard(); d["quota_status"]["codex"]["reset_entitlements"]["items"] = [{"status": "available", "display_name": "Full reset"}, {"status": "used"}]; self.assertEqual(len(cli.reset_data(d)["items"]), 1)
    def test_prices_current_models(self): self.assertEqual(len(cli.prices_data("codex", json.loads((cli.RUNTIME_DIR / "settings.json").read_text()), False)), 4)
    def test_prices_legacy_models(self): self.assertEqual(len(cli.prices_data("codex", json.loads((cli.RUNTIME_DIR / "settings.json").read_text()), True)), 6)
    def test_prices_tiered_gemini(self): self.assertIsNotNone(cli.prices_data("antigravity", json.loads((cli.RUNTIME_DIR / "settings.json").read_text()), False)[3]["tiered_pricing"])
    def test_prices_unpriced_oss(self): self.assertTrue(cli.prices_data("antigravity", json.loads((cli.RUNTIME_DIR / "settings.json").read_text()), False)[4]["unpriced"])
    def test_dashboard_missing(self):
        (cli.RUNTIME_DIR / "dashboard.json").unlink(); code, out = self.run_main("status", "--json"); self.assertEqual(code, 3); self.assertFalse(json.loads(out)["ok"])
    def test_dashboard_corrupt(self):
        (cli.RUNTIME_DIR / "dashboard.json").write_text("{", encoding="utf-8"); self.assertEqual(self.run_main("status")[0], 3)
    def test_old_dashboard_without_resets(self):
        d = dashboard(); d["quota_status"]["codex"].pop("reset_entitlements"); self.assertIsNone(cli.reset_data(d)["available_count"])
    def test_settings_missing(self):
        (cli.RUNTIME_DIR / "settings.json").unlink(); self.assertEqual(self.run_main("prices")[0], 3)
    def test_settings_corrupt(self):
        (cli.RUNTIME_DIR / "settings.json").write_text("{", encoding="utf-8"); self.assertEqual(self.run_main("prices")[0], 3)
    def test_json_schema_version(self): self.assertEqual(json.loads(self.run_main("usage", "--json")[1])["schema_version"], 1)
    def test_json_stdout_is_parseable(self): self.assertIsInstance(json.loads(self.run_main("quota", "--json")[1]), dict)
    def test_no_reset_write_operation(self): self.assertNotIn("redeem", Path(cli.__file__).read_text())
    def test_no_webview(self): self.assertNotIn("WebView", Path(cli.__file__).read_text())
    def test_no_accessibility(self): self.assertNotIn("Accessibility", Path(cli.__file__).read_text())
    def test_no_localhost(self): self.assertNotIn("localhost", Path(cli.__file__).read_text())
    def test_no_documents_dependency(self): self.assertNotIn("Documents/Antigravity", Path(cli.__file__).read_text())
    def test_refresh_parser_default_timeout(self): self.assertEqual(cli.build_parser().parse_args(["refresh"]).timeout, 90)
    def test_doctor_is_read_only(self):
        before = {p.name: p.read_bytes() for p in cli.RUNTIME_DIR.iterdir()}; cli.doctor_data(); after = {p.name: p.read_bytes() for p in cli.RUNTIME_DIR.iterdir()}; self.assertEqual(before, after)
    def test_current_dashboard_values_are_direct(self): self.assertEqual(cli.usage_data("codex", "today", dashboard())["codex"]["identifiable_tokens"], 15)
    def test_cost_is_not_recalculated(self): self.assertEqual(cli.usage_data("codex", "today", dashboard())["codex"]["estimated_cost"], 1.25)
    def test_quota_preserves_source_path(self): self.assertEqual(cli.quota_data("antigravity", dashboard())["antigravity"]["items"][0]["source_path"], "rpc")
    def test_quota_preserves_original_field(self): self.assertEqual(cli.quota_data("antigravity", dashboard())["antigravity"]["items"][0]["original_field_name"], "bucket.remaining.remainingFraction")
    def test_reset_does_not_expose_id(self):
        d = dashboard(); d["quota_status"]["codex"]["reset_entitlements"]["items"] = [{"id": "secret", "status": "available", "display_name": "Full reset"}]; self.assertNotIn("id", cli.reset_data(d)["items"][0])
    def test_reset_expires_display_time(self):
        d = dashboard(); d["quota_status"]["codex"]["reset_entitlements"]["items"] = [{"status": "available", "expires_at": "2026-07-20T00:00:00Z"}]; self.assertTrue(cli.reset_data(d)["items"][0]["display_time"])
    def test_status_dashboard_time(self): self.assertEqual(cli.status_data(dashboard())["dashboard_updated_at"], "2026-07-19T10:00:00+08:00")
    def test_source_names_all(self): self.assertEqual(cli.source_names("all"), ["antigravity", "codex"])
    def test_source_names_specific(self): self.assertEqual(cli.source_names("codex"), ["codex"])
    def test_range_mapping(self): self.assertEqual(cli.range_key("30d"), "last_30")
    def test_cli_version(self): self.assertRegex(cli.CLI_VERSION, r"^\d+\.\d+\.\d+$")
    def test_app_bundle_cli_target(self): self.assertTrue(str(cli.BUNDLE_CLI).endswith("quotaview_cli.py"))
    def test_no_token_or_cookie_fields_in_reset_output(self):
        encoded = json.dumps(cli.reset_data(dashboard()), ensure_ascii=False); self.assertNotIn("token", encoded.lower()); self.assertNotIn("cookie", encoded.lower())


if __name__ == "__main__":
    unittest.main()
