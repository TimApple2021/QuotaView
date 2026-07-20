import copy
from pathlib import Path
from unittest.mock import patch

import monitor_backend as m


LIVE_AT = "2026-07-20T10:00:00Z"
ATTEMPT_AT = "2026-07-20T10:01:00Z"


def live_quota():
    return {
        "status": "official_live",
        "message": "",
        "items": [{
            "name": "Codex Weekly Quota",
            "group": "chatgpt_plus",
            "window": "weekly",
            "used_percent": 28,
            "reset_time": "2026-07-27T00:00:00Z",
            "confidence": "official_live",
            "observed_at": LIVE_AT,
        }],
        "reset_entitlements": {
            "status": "official_live",
            "available_count": 1,
            "items": [{"status": "available", "display_name": "Full reset", "expires_at": "2026-08-01T00:00:00Z"}],
            "observed_at": LIVE_AT,
        },
    }


def failed_quota():
    return {
        "status": "unavailable",
        "message": "暂时无法读取当前官方额度",
        "items": [],
        "reset_entitlements": {"status": "unavailable", "available_count": None, "items": []},
    }


def test_success_then_transient_failure_preserves_quota_and_reset():
    stale = m._merge_quota_snapshot("codex", failed_quota(), live_quota(), ATTEMPT_AT)
    assert stale["status"] == "official_stale"
    assert stale["items"][0]["used_percent"] == 28
    assert stale["reset_entitlements"]["status"] == "official_stale"
    assert stale["reset_entitlements"]["available_count"] == 1
    assert stale["last_success_at"] == LIVE_AT
    assert stale["last_attempt_at"] == ATTEMPT_AT


def test_never_successful_source_remains_unavailable():
    unavailable = m._merge_quota_snapshot("codex", failed_quota(), {}, ATTEMPT_AT)
    assert unavailable["status"] == "unavailable"
    assert unavailable["items"] == []
    assert unavailable["last_error_code"]


def test_later_success_recovers_live_and_clears_error():
    stale = m._merge_quota_snapshot("codex", failed_quota(), live_quota(), ATTEMPT_AT)
    recovered = m._merge_quota_snapshot("codex", live_quota(), stale, "2026-07-20T10:02:00Z")
    assert recovered["status"] == "official_live"
    assert "last_error_code" not in recovered
    assert recovered["reset_entitlements"]["status"] == "official_live"


def test_antigravity_and_codex_failures_are_isolated():
    previous = {"quota_status": {"codex": live_quota(), "antigravity": live_quota()}}
    with patch.object(m, "read_antigravity_live_quota", return_value=failed_quota()), patch.object(m, "read_codex_app_server_quota", return_value=failed_quota()), patch.object(m.time, "sleep", return_value=None):
        merged = m.get_quota_status({}, [], previous_dashboard=previous)
    assert set(merged) == {"antigravity", "codex"}


def test_empty_local_scan_does_not_replace_nonzero_history():
    result = {"sources": {"antigravity": {"all_time": {"identifiable_tokens": 0}}, "codex": {"all_time": {"identifiable_tokens": 4}}}}
    previous = {"sources": {"antigravity": {"all_time": {"identifiable_tokens": 99}}, "codex": {"all_time": {"identifiable_tokens": 3}}}}
    kept = m._preserve_nonzero_source_stats(result, previous)
    assert kept["sources"]["antigravity"]["all_time"]["identifiable_tokens"] == 99
    assert kept["sources"]["codex"]["all_time"]["identifiable_tokens"] == 4


def test_retry_backoff_is_bounded_and_reaches_success():
    calls = []
    sleeps = []

    def reader(_timeout):
        calls.append(len(calls))
        return failed_quota() if len(calls) < 3 else live_quota()

    result = m._read_with_retries(reader, total_timeout=10, sleep_fn=sleeps.append)
    assert result["status"] == "official_live"
    assert len(calls) == 3
    assert sleeps == [0.5, 1.0]


def test_first_failure_then_success_recovers_live_without_erasing_cache():
    calls = []
    sequence = [failed_quota(), live_quota()]

    def reader(_timeout):
        calls.append(1)
        return sequence.pop(0)

    previous = {"quota_status": {"codex": live_quota(), "antigravity": {}}}
    with patch.object(m, "read_antigravity_live_quota", return_value=live_quota()), patch.object(m, "read_codex_app_server_quota", side_effect=reader), patch.object(m.time, "sleep", return_value=None):
        result = m.get_quota_status({}, [], previous_dashboard=previous)
    assert result["codex"]["status"] == "official_live"
    assert result["codex"]["reset_entitlements"]["status"] == "official_live"
    assert len(calls) == 2


def test_first_two_failures_then_success_uses_three_attempts():
    calls = []
    sequence = [failed_quota(), failed_quota(), live_quota()]

    def reader(_timeout):
        calls.append(1)
        return sequence.pop(0)

    with patch.object(m, "read_antigravity_live_quota", return_value=live_quota()), patch.object(m, "read_codex_app_server_quota", side_effect=reader), patch.object(m.time, "sleep", return_value=None):
        result = m.get_quota_status({}, [], previous_dashboard={"quota_status": {}})
    assert result["codex"]["status"] == "official_live"
    assert len(calls) == 3


def test_three_retry_failures_stop_and_do_not_loop():
    calls = []
    sleeps = []

    def reader(_timeout):
        calls.append(1)
        return failed_quota()

    result = m._read_with_retries(reader, total_timeout=10, sleep_fn=sleeps.append)
    assert result["status"] == "unavailable"
    assert len(calls) == 4
    assert sleeps == [0.5, 1.0, 2.0]


def test_permanent_error_is_not_retried():
    calls = []

    def reader(_timeout):
        calls.append(1)
        return {"status": "unavailable", "items": [], "last_error_code": "authentication_failure"}

    result = m._read_with_retries(reader, total_timeout=10, sleep_fn=lambda _delay: None)
    assert result["last_error_code"] == "authentication_failure"
    assert len(calls) == 1


def test_cli_and_ui_contracts_expose_stale_state():
    cli = Path("cli/quotaview_cli.py").read_text(encoding="utf-8")
    menu = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
    assert "last_success_at" in cli and "last_attempt_at" in cli and "last_error_code" in cli
    assert "official_stale" in menu
    assert "暂时无法更新，显示上次成功数据" in menu
    assert "Unable to refresh; showing last successful data" in menu


def test_backup_recovery_is_present_and_runtime_path_is_unchanged():
    reader = Path("macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text(encoding="utf-8")
    assert "dashboardBackupPath" in reader
    assert "restorePrimaryDashboard" in reader
    assert 'appendingPathComponent("Antigravity Token Monitor"' in reader
