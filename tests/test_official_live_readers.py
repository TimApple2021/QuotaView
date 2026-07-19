import copy
import unittest
from pathlib import Path
from unittest.mock import patch

import monitor_backend as m


class TestOfficialLiveReaders(unittest.TestCase):
    observed_a = "2026-07-18T01:00:00Z"
    observed_b = "2026-07-18T01:01:00Z"

    @staticmethod
    def ag_payload():
        return {
            "response": {
                "groups": [
                    {"displayName": "Gemini Models", "buckets": [
                        {"window": "weekly", "remainingFraction": 0.23, "resetTime": "2026-07-20T01:00:00Z"},
                        {"window": "5h", "remainingFraction": 0.23, "resetTime": "2026-07-18T03:00:00Z"},
                    ]},
                    {"displayName": "Claude and GPT models", "buckets": [
                        {"window": "weekly", "remainingFraction": 0.23, "resetTime": "2026-07-22T01:00:00Z"},
                        {"window": "5h", "remainingFraction": 0.23, "resetTime": "2026-07-18T03:00:00Z"},
                    ]},
                ]
            }
        }

    @staticmethod
    def codex_result(raw=17):
        return {
            "rateLimitsByLimitId": {
                "codex": {
                    "limitId": "codex",
                    "planType": "plus",
                    "primary": {
                        "usedPercent": raw,
                        "windowDurationMins": 10_080,
                        "resetsAt": 1_785_000_000,
                    },
                }
            }
        }

    def test_antigravity_production_has_no_current_snapshot_hardcoding(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8")
        for value in (
            "2026-07-20T05:42:39Z",
            "2026-07-18T13:51:39Z",
            "2026-07-22T07:42:39Z",
            "2026-07-18T13:57:39Z",
        ):
            self.assertNotIn(value, source)
        self.assertNotIn('raw_percent": 34', source)
        self.assertNotIn('raw_percent": 52', source)

    def test_antigravity_snapshot_is_independent_of_models_page_state(self):
        live = m.normalize_antigravity_quota_rpc_response(self.ag_payload(), self.observed_a)
        after_page_close = m.normalize_antigravity_quota_rpc_response(self.ag_payload(), self.observed_b)
        self.assertEqual(live["status"], "official_live")
        self.assertEqual(after_page_close["status"], "official_live")
        self.assertEqual(len(after_page_close["items"]), 4)

    def test_antigravity_reopen_updates_observed_at(self):
        first = m.normalize_antigravity_quota_rpc_response(self.ag_payload(), self.observed_a)
        reopened = m.normalize_antigravity_quota_rpc_response(self.ag_payload(), self.observed_b)
        self.assertEqual({x["observed_at"] for x in first["items"]}, {self.observed_a})
        self.assertEqual({x["observed_at"] for x in reopened["items"]}, {self.observed_b})

    def test_antigravity_rpc_uses_current_reset_time(self):
        payload = self.ag_payload()
        payload["response"]["groups"][0]["buckets"][0]["resetTime"] = "2026-07-21T01:00:00Z"
        current = m.normalize_antigravity_quota_rpc_response(payload, self.observed_b)
        self.assertEqual(current["items"][0]["reset_time"], "2026-07-21T01:00:00Z")

    def test_production_reader_never_uses_screenshot_or_task_text(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8")
        self.assertNotIn("document.body.innerText", source)
        self.assertNotIn("screenshot", source.lower())
        self.assertNotIn("task text", source.lower())

    def test_codex_historical_log_cannot_enter_official_reader(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8")
        function = source[source.index("def read_codex_app_server_quota"):source.index("def get_quota_status", source.index("def read_codex_app_server_quota"))]
        self.assertNotIn("jsonl", function.lower())
        self.assertNotIn("historical_log", function)

    @patch.object(m, "read_codex_app_server_quota", return_value={"status": "unavailable", "message": "暂时无法读取当前官方额度", "items": []})
    @patch.object(m, "read_antigravity_live_quota", return_value={"status": "unavailable", "message": "暂时无法读取官方额度", "items": []})
    def test_codex_without_official_live_keeps_safe_placeholder(self, _ag, _codex):
        status = m.get_quota_status({}, [])["codex"]
        self.assertEqual(status["status"], "unavailable")
        self.assertEqual(status["message"], "暂时无法读取当前官方额度")
        self.assertEqual(status["items"], [])

    def test_codex_remaining_semantics_converts_to_used(self):
        self.assertEqual(m.codex_used_percent(91, "remaining"), 9)

    def test_codex_app_server_used_semantics_is_not_inverted(self):
        status = m.normalize_codex_app_server_rate_limits(self.codex_result(17), self.observed_a)
        item = status["items"][0]
        self.assertEqual(item["raw_percent"], 17)
        self.assertEqual(item["used_percent"], 17)
        self.assertEqual(item["percent_semantics"], "used")

    def test_codex_official_fields_and_source_path(self):
        item = m.normalize_codex_app_server_rate_limits(self.codex_result(), self.observed_a)["items"][0]
        self.assertEqual(item["group"], "chatgpt_plus")
        self.assertEqual(item["window"], "weekly")
        self.assertEqual(item["confidence"], "official_live")
        self.assertEqual(item["original_field_name"], "rateLimitsByLimitId.codex.primary.usedPercent")
        self.assertEqual(item["source_path"], "codex_app_server_rpc")

    def test_quota_readers_do_not_mutate_token_or_cost_data(self):
        totals = {"input": 313_526_456, "output": 24_760_861, "cost": 768.7211715}
        before = copy.deepcopy(totals)
        m.normalize_antigravity_quota_rpc_response(self.ag_payload(), self.observed_a)
        m.normalize_codex_app_server_rate_limits(self.codex_result(), self.observed_a)
        self.assertEqual(totals, before)

    def test_consecutive_snapshots_do_not_accumulate_items(self):
        first = m.normalize_codex_app_server_rate_limits(self.codex_result(17), self.observed_a)
        second = m.normalize_codex_app_server_rate_limits(self.codex_result(18), self.observed_b)
        self.assertEqual(len(first["items"]), 1)
        self.assertEqual(len(second["items"]), 1)
        self.assertEqual(second["items"][0]["raw_percent"], 18)


if __name__ == "__main__":
    unittest.main()
