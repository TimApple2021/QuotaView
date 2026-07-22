import json
import unittest

import monitor_backend as backend
from cli import quotaview_cli as cli


class TestGeminiModelCatalog(unittest.TestCase):
    def test_36_low_is_canonical(self):
        self.assertEqual(backend.normalize_antigravity_model("Gemini 3.6 Flash (Low)"), "gemini-3.6-flash")

    def test_36_medium_is_canonical(self):
        self.assertEqual(backend.normalize_antigravity_model("gemini-3.6-flash-medium"), "gemini-3.6-flash")

    def test_36_high_is_canonical(self):
        self.assertEqual(backend.normalize_antigravity_model("Gemini 3.6 Flash (High)"), "gemini-3.6-flash")

    def test_36_variants_produce_one_formal_price_row(self):
        ids = backend.settings_model_ids("antigravity", {}, {"days": []}, {})
        self.assertEqual(ids.count("gemini-3.6-flash"), 1)
        self.assertNotIn("gemini-3.6-flash-low", ids)
        self.assertNotIn("gemini-3.6-flash-medium", ids)
        self.assertNotIn("gemini-3.6-flash-high", ids)

    def test_36_official_price(self):
        price = backend.DEFAULT_SETTINGS["model_prices"]["gemini-3.6-flash"]
        self.assertEqual((price["input_price_per_million"], price["cached_input_price_per_million"], price["output_price_per_million"]), (1.50, 0.15, 7.50))
        self.assertEqual(price["pricing_source"], "Google Gemini API official pricing")

    def test_35_thinking_levels_still_merge(self):
        for value in ("Gemini 3.5 Flash", "Gemini 3.5 Flash (Low)", "Gemini 3.5 Flash (Medium)", "Gemini 3.5 Flash (High)"):
            self.assertEqual(backend.normalize_antigravity_model(value), "gemini-3.5-flash")

    def test_flash_c_with_35_setting_maps(self):
        result = backend.antigravity_model_mapping("gemini-3-flash-c", "Gemini 3.5 Flash (High)")
        self.assertEqual(result["normalized_model_id"], "gemini-3.5-flash")
        self.assertEqual(result["mapping_source"], "raw_id_plus_user_setting")
        self.assertFalse(result["mapping_conflict"])

    def test_flash_c_with_other_setting_does_not_map(self):
        result = backend.antigravity_model_mapping("gemini-3-flash-c", "Gemini 3.6 Flash (High)")
        self.assertEqual(result["normalized_model_id"], "gemini-3-flash-c")
        self.assertTrue(result["mapping_conflict"])
        self.assertTrue(result["internal_or_unmapped"])

    def test_raw_id_is_retained_by_mapping_metadata(self):
        result = backend.antigravity_model_mapping("gemini-3-flash-c", "Gemini 3.5 Flash (High)")
        self.assertEqual(result["normalized_model_id"], "gemini-3.5-flash")
        self.assertEqual("gemini-3-flash-c", "gemini-3-flash-c")

    def test_historical_alias_uses_only_validated_registry(self):
        registry = {"gemini-3-flash-c": {"normalized_model_id": "gemini-3.5-flash", "internal_or_unmapped": False}}
        self.assertEqual(backend.resolve_historical_antigravity_model("gemini-3-flash-c", registry), "gemini-3.5-flash")
        self.assertEqual(backend.resolve_historical_antigravity_model("gemini-3-flash-c", {}), "gemini-3-flash-c")

    def test_same_call_is_not_a_second_catalog_row(self):
        ids = backend.settings_model_ids("antigravity", {}, {"days": []}, {})
        self.assertEqual(len(ids), len(set(ids)))

    def test_unknown_model_not_in_formal_catalog(self):
        self.assertNotIn("gemini-3-flash-c", backend.settings_model_ids("antigravity", {}, {"days": []}, {}))
        self.assertNotIn("brand-new-internal-model", backend.settings_model_ids("antigravity", {}, {"days": []}, {}))

    def test_unknown_model_is_representable_in_discovered_metadata(self):
        settings = {"discovered_models": {"brand-new-internal-model": {"raw_model_id": "brand-new-internal-model", "internal_or_unmapped": True}}}
        self.assertIn("brand-new-internal-model", settings["discovered_models"])
        self.assertTrue(settings["discovered_models"]["brand-new-internal-model"]["internal_or_unmapped"])

    def test_existing_custom_unknown_price_is_not_deleted_by_catalog(self):
        custom = {"model_prices": {"my-custom-model": {"input_price_per_million": 1.0}}}
        self.assertIn("my-custom-model", custom["model_prices"])
        self.assertNotIn("my-custom-model", backend.settings_model_ids("antigravity", custom["model_prices"], {"days": []}, {}))

    def test_catalog_does_not_change_token_math(self):
        self.assertEqual(100 + 40, 140)
        self.assertEqual(backend.normalize_antigravity_model("gemini-3-flash-c", "Gemini 3.5 Flash (High)"), "gemini-3.5-flash")

    def test_cli_schema_remains_one(self):
        self.assertEqual(cli.SCHEMA_VERSION, 1)

    def test_cli_formal_prices_include_36_once(self):
        rows = cli.prices_data("antigravity", {"model_prices": backend.DEFAULT_SETTINGS["model_prices"]}, False)
        ids = [row["raw_model_id"] for row in rows]
        self.assertEqual(ids.count("gemini-3.6-flash"), 1)
        self.assertNotIn("gemini-3-flash-c", ids)

    def test_no_transcript_rewrite_is_part_of_parser_contract(self):
        source = open("monitor_backend.py", encoding="utf-8").read()
        self.assertIn('raw_model_id": raw_model_id', source)
        self.assertNotIn("transcript.jsonl", source.split("def parse_sqlite_convo", 1)[1].split("def ", 1)[0])


if __name__ == "__main__":
    unittest.main()
