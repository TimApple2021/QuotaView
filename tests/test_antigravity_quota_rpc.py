import copy
import json
import struct
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import monitor_backend as m


OBSERVED = "2026-07-18T12:00:00Z"


def rpc_payload(fraction=0.37):
    return {
        "response": {
            "groups": [
                {
                    "displayName": "Gemini Models",
                    "buckets": [
                        {"bucketId": "gemini-weekly", "window": "weekly", "remainingFraction": fraction, "resetTime": "2026-07-20T06:00:00Z"},
                        {"bucketId": "gemini-5h", "window": "5h", "remainingFraction": 0.08, "resetTime": "2026-07-18T14:00:00Z"},
                    ],
                },
                {
                    "displayName": "Claude and GPT models",
                    "buckets": [
                        {"bucketId": "3p-weekly", "window": "weekly", "remainingFraction": 0.12, "resetTime": "2026-07-22T08:00:00Z"},
                        {"bucketId": "3p-5h", "window": "5h", "remainingFraction": 0.52, "resetTime": "2026-07-18T15:00:00Z"},
                    ],
                },
            ]
        }
    }


class ResponseContext:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class TestAntigravityQuotaRPC(unittest.TestCase):
    def test_rpc_path_is_official_language_server_method(self):
        self.assertEqual(m.ANTIGRAVITY_QUOTA_RPC_PATH, "/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary")

    def test_grpc_web_json_request_round_trip(self):
        payload = {"forceRefresh": True}
        self.assertEqual(m.decode_grpc_web_json_message(m.encode_grpc_web_json_message(payload)), payload)

    def test_decoder_ignores_trailer_after_data(self):
        data = m.encode_grpc_web_json_message({"response": {}})
        trailer = b"grpc-status: 0\r\n"
        framed_trailer = b"\x80" + struct.pack(">I", len(trailer)) + trailer
        self.assertEqual(m.decode_grpc_web_json_message(data + framed_trailer), {"response": {}})

    def test_decoder_rejects_truncated_frame(self):
        with self.assertRaises(ValueError):
            m.decode_grpc_web_json_message(b"\x00\x00\x00\x00\x20{}")

    def test_decoder_rejects_empty_response(self):
        with self.assertRaises(ValueError):
            m.decode_grpc_web_json_message(b"")

    def test_all_four_buckets_are_returned_in_fixed_order(self):
        items = m.normalize_antigravity_quota_rpc_response(rpc_payload(), OBSERVED)["items"]
        self.assertEqual([(x["group"], x["window"]) for x in items], m.ANTIGRAVITY_QUOTA_ORDER)

    def test_remaining_fraction_is_rounded_to_raw_percent(self):
        item = m.normalize_antigravity_quota_rpc_response(rpc_payload(0.34489173), OBSERVED)["items"][0]
        self.assertEqual(item["raw_percent"], 34)

    def test_remaining_percent_is_inverted_to_used(self):
        item = m.normalize_antigravity_quota_rpc_response(rpc_payload(0.34), OBSERVED)["items"][0]
        self.assertEqual(item["used_percent"], 66)
        self.assertEqual(item["percent_semantics"], "remaining")

    def test_reset_time_comes_from_rpc(self):
        item = m.normalize_antigravity_quota_rpc_response(rpc_payload(), OBSERVED)["items"][0]
        self.assertEqual(item["reset_time"], "2026-07-20T06:00:00Z")

    def test_missing_reset_makes_snapshot_unavailable(self):
        payload = rpc_payload()
        payload["response"]["groups"][0]["buckets"][0]["resetTime"] = ""
        self.assertEqual(m.normalize_antigravity_quota_rpc_response(payload, OBSERVED)["status"], "unavailable")

    def test_fraction_above_one_is_rejected(self):
        self.assertEqual(m.normalize_antigravity_quota_rpc_response(rpc_payload(1.01), OBSERVED)["status"], "unavailable")

    def test_fraction_below_zero_is_rejected(self):
        self.assertEqual(m.normalize_antigravity_quota_rpc_response(rpc_payload(-0.01), OBSERVED)["status"], "unavailable")

    def test_duplicate_group_window_is_deduplicated(self):
        payload = rpc_payload()
        payload["response"]["groups"][0]["buckets"].append(copy.deepcopy(payload["response"]["groups"][0]["buckets"][0]))
        items = m.normalize_antigravity_quota_rpc_response(payload, OBSERVED)["items"]
        self.assertEqual(len(items), 4)

    def test_unknown_group_is_ignored(self):
        payload = rpc_payload()
        payload["response"]["groups"].append({"displayName": "Other", "buckets": []})
        self.assertEqual(len(m.normalize_antigravity_quota_rpc_response(payload, OBSERVED)["items"]), 4)

    def test_unknown_window_is_ignored(self):
        payload = rpc_payload()
        payload["response"]["groups"][0]["buckets"][0]["window"] = "daily"
        self.assertEqual(m.normalize_antigravity_quota_rpc_response(payload, OBSERVED)["status"], "unavailable")

    def test_observed_at_is_shared_by_all_items(self):
        items = m.normalize_antigravity_quota_rpc_response(rpc_payload(), OBSERVED)["items"]
        self.assertEqual({x["observed_at"] for x in items}, {OBSERVED})

    def test_official_metadata_is_preserved(self):
        item = m.normalize_antigravity_quota_rpc_response(rpc_payload(), OBSERVED)["items"][0]
        self.assertEqual(item["confidence"], "official_live")
        self.assertEqual(item["original_field_name"], "bucket.remaining.remainingFraction")
        self.assertEqual(
            item["source_path"],
            "language_server_rpc:/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary",
        )

    @patch.object(m, "find_antigravity_cdp_port", return_value=None)
    def test_missing_cdp_has_no_rpc_origin(self, _port):
        self.assertEqual(m.discover_antigravity_rpc_origin(), "")

    @patch("urllib.request.urlopen")
    def test_rpc_origin_comes_from_live_page_target(self, urlopen):
        response = ResponseContext(json.dumps([{"type": "page", "url": "https://127.0.0.1:45678/c/id"}]).encode())
        urlopen.return_value = response
        self.assertEqual(m.discover_antigravity_rpc_origin(12345), "https://127.0.0.1:45678")

    @patch.object(m.subprocess, "check_output", return_value="/Applications/Antigravity.app/Contents/Resources/bin/language_server --standalone --csrf_token ephemeral-value\n")
    def test_local_csrf_value_is_read_from_running_process(self, _check):
        self.assertEqual(m.find_antigravity_language_server_csrf_token(), "ephemeral-value")

    @patch.object(m, "discover_antigravity_rpc_origin", return_value="")
    def test_antigravity_not_running_is_unavailable(self, _origin):
        self.assertEqual(m.read_antigravity_live_quota()["status"], "unavailable")

    @patch.object(m, "find_antigravity_language_server_csrf_token", return_value="")
    @patch.object(m, "discover_antigravity_rpc_origin", return_value="https://127.0.0.1:45678")
    def test_missing_local_csrf_value_is_unavailable(self, _origin, _token):
        self.assertEqual(m.read_antigravity_live_quota()["status"], "unavailable")

    @patch("urllib.request.urlopen")
    @patch.object(m, "find_antigravity_language_server_csrf_token", return_value="ephemeral")
    @patch.object(m, "discover_antigravity_rpc_origin", return_value="https://127.0.0.1:45678")
    def test_reader_posts_force_refresh_to_rpc(self, _origin, _token, urlopen):
        urlopen.return_value = ResponseContext(m.encode_grpc_web_json_message(rpc_payload()))
        status = m.read_antigravity_live_quota()
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://127.0.0.1:45678" + m.ANTIGRAVITY_QUOTA_RPC_PATH)
        self.assertEqual(m.decode_grpc_web_json_message(request.data), {"forceRefresh": True})
        self.assertEqual(status["status"], "official_live")

    def test_production_reader_has_no_dom_or_screenshot_extraction(self):
        source = Path("monitor_backend.py").read_text(encoding="utf-8")
        for forbidden in ("document.body.innerText", "__reactFiber", "querySelector", "screenshot"):
            self.assertNotIn(forbidden, source)

    def test_quota_normalization_does_not_mutate_token_summary(self):
        summary = {"input": 313_526_456, "output": 24_760_861, "cost": 768.7211715}
        before = copy.deepcopy(summary)
        m.normalize_antigravity_quota_rpc_response(rpc_payload(), OBSERVED)
        self.assertEqual(summary, before)

    def test_application_support_runtime_path_remains_enabled(self):
        build = Path("macos/build.sh").read_text(encoding="utf-8")
        self.assertIn("Application Support/Antigravity Token Monitor", build)


if __name__ == "__main__":
    unittest.main()
