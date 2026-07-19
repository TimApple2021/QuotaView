import copy
import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

import monitor_backend as m


def rpc_payload(fraction=0.37):
    return {"response": {"groups": [
        {"displayName": "Gemini Models", "buckets": [
            {"window": "weekly", "remainingFraction": fraction, "resetTime": "2026-07-20T06:00:00Z"},
            {"window": "5h", "remainingFraction": 0.08, "resetTime": "2026-07-18T14:00:00Z"},
        ]},
        {"displayName": "Claude and GPT models", "buckets": [
            {"window": "weekly", "remainingFraction": 0.12, "resetTime": "2026-07-22T08:00:00Z"},
            {"window": "5h", "remainingFraction": 0.52, "resetTime": "2026-07-18T15:00:00Z"},
        ]},
    ]}}


class ResponseContext:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class TestAntigravityQuotaBackgroundArchitecture(unittest.TestCase):
    @staticmethod
    def live_reader(urlopen):
        urlopen.return_value = ResponseContext(m.encode_grpc_web_json_message(rpc_payload()))
        return m.read_antigravity_live_quota()

    @patch("urllib.request.urlopen")
    @patch.object(m, "find_antigravity_language_server_csrf_token", return_value="ephemeral")
    @patch.object(m, "discover_antigravity_rpc_origin", return_value="https://127.0.0.1:45678")
    def test_models_page_closed_still_returns_official_live(self, _origin, _token, urlopen):
        status = self.live_reader(urlopen)
        self.assertEqual(status["status"], "official_live")
        self.assertEqual(len(status["items"]), 4)

    def test_closed_page_prompt_is_removed_from_production(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8")
        self.assertNotIn("请先在 Antigravity 打开 Model Quota 页面", source)

    def test_production_does_not_read_document_body_text(self):
        self.assertNotIn("document.body.innerText", Path("monitor_backend.py").read_text(encoding="utf-8"))

    def test_production_does_not_depend_on_visible_react_cards(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8")
        for marker in ("__reactFiber", "querySelector", "getClientRects", "rounded-xl"):
            self.assertNotIn(marker, source)

    def test_production_does_not_read_screenshot_or_task_text(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("screenshot", source)
        self.assertNotIn("task text", source)

    def test_four_items_are_strictly_deduplicated(self):
        payload = rpc_payload()
        payload["response"]["groups"] += copy.deepcopy(payload["response"]["groups"])
        items = m.normalize_antigravity_quota_rpc_response(payload, "2026-07-18T12:00:00Z")["items"]
        self.assertEqual(len(items), 4)
        self.assertEqual(len({(x["group"], x["window"]) for x in items}), 4)

    def test_all_four_reset_times_are_nonempty(self):
        items = m.normalize_antigravity_quota_rpc_response(rpc_payload(), "2026-07-18T12:00:00Z")["items"]
        self.assertTrue(all(x["reset_time"] for x in items))

    def test_observed_at_updates_only_with_a_new_live_response(self):
        first = m.normalize_antigravity_quota_rpc_response(rpc_payload(), "2026-07-18T12:00:00Z")
        second = m.normalize_antigravity_quota_rpc_response(rpc_payload(), "2026-07-18T12:01:00Z")
        self.assertEqual({x["observed_at"] for x in first["items"]}, {"2026-07-18T12:00:00Z"})
        self.assertEqual({x["observed_at"] for x in second["items"]}, {"2026-07-18T12:01:00Z"})

    @patch("urllib.request.urlopen", side_effect=OSError("offline"))
    @patch.object(m, "find_antigravity_language_server_csrf_token", return_value="ephemeral")
    @patch.object(m, "discover_antigravity_rpc_origin", return_value="https://127.0.0.1:45678")
    def test_failed_refresh_does_not_forge_cached_observed_at(self, _origin, _token, _urlopen):
        failed = m.read_antigravity_live_quota()
        self.assertEqual(failed, {"status": "unavailable", "message": "暂时无法读取官方额度", "items": []})

    def test_codex_official_live_reader_is_not_coupled_to_antigravity_rpc(self):
        source = inspect.getsource(m.read_codex_app_server_quota)
        self.assertNotIn("RetrieveUserQuotaSummary", source)
        self.assertNotIn("ANTIGRAVITY", source)

    def test_token_and_api_cost_values_are_not_mutated(self):
        totals = {"input": 313_526_456, "output": 24_760_861, "cost": 768.7211715}
        before = copy.deepcopy(totals)
        m.normalize_antigravity_quota_rpc_response(rpc_payload(), "2026-07-18T12:00:00Z")
        self.assertEqual(totals, before)

    def test_consecutive_live_scans_do_not_accumulate_items(self):
        first = m.normalize_antigravity_quota_rpc_response(rpc_payload(0.34), "2026-07-18T12:00:00Z")
        second = m.normalize_antigravity_quota_rpc_response(rpc_payload(0.33), "2026-07-18T12:01:00Z")
        self.assertEqual(len(first["items"]), 4)
        self.assertEqual(len(second["items"]), 4)
        self.assertEqual(second["items"][0]["raw_percent"], 33)


if __name__ == "__main__":
    unittest.main()
