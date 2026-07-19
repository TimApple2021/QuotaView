import json
from pathlib import Path

import monitor_backend as backend


ROOT = Path(__file__).resolve().parents[1]


def official_result(plan_type="plus"):
    return {
        "rateLimitsByLimitId": {"codex": {
            "planType": plan_type,
            "primary": {"usedPercent": 12, "windowDurationMins": 10080, "resetsAt": 1785000000},
        }}
    }


def test_known_official_plan_names_are_normalized_without_multipliers():
    expected = {"free": "Free", "go": "Go", "plus": "Plus", "pro": "Pro",
                "business": "Business", "team": "Team", "enterprise": "Enterprise",
                "edu": "Edu", "education": "Edu"}
    for raw, display in expected.items():
        metadata = backend.codex_plan_metadata(raw, "codex_app_server_rpc", "official_live")
        assert metadata["plan_display_name"] == display
        assert metadata["plan_confidence"] == "official_live"


def test_unknown_plan_does_not_fallback_to_plus():
    assert backend.normalize_codex_plan_type("mystery") == "unknown"
    item = backend.normalize_codex_app_server_rate_limits(official_result("mystery"), "2026-07-19T00:00:00Z")["items"][0]
    assert item["plan_type"] == "unknown"
    assert "Plus" not in item["name"]


def test_official_plan_wins_and_reports_non_sensitive_mismatch():
    status = backend.normalize_codex_app_server_rate_limits(official_result("pro"), "2026-07-19T00:00:00Z")
    status = backend._apply_codex_plan_metadata(status, {"plan_type": "plus"})
    assert status["plan_type"] == "pro"
    assert status["plan_mismatch"] == {
        "official_plan_type": "pro", "local_plan_type": "plus",
        "official_source": "codex_app_server_rpc", "local_source": "codex_local_event",
    }


def test_local_plan_is_explicit_fallback():
    status = backend.normalize_codex_app_server_rate_limits(official_result(None), "2026-07-19T00:00:00Z")
    status = backend._apply_codex_plan_metadata(status, {"plan_type": "go"})
    assert status["plan_type"] == "go"
    assert status["plan_source"] == "codex_local_event"
    assert status["plan_confidence"] == "local_observed"
    assert status["items"][0]["name"] == "ChatGPT Go 周额度"


def test_cli_schema_stays_one_and_exposes_plan_fields():
    cli = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")
    assert "SCHEMA_VERSION = 1" in cli
    for field in ("plan_type", "plan_display_name", "plan_source", "plan_confidence"):
        assert field in cli


def test_swift_has_structured_plan_fields_and_bilingual_titles():
    reader = (ROOT / "macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text(encoding="utf-8")
    model = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
    view = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
    for field in ("planType", "planDisplayName", "planSource", "planConfidence"):
        assert field in reader
    assert "Weekly Quota" in model and "Codex 周额度" in model
    assert "Expires" in view and "到期" in view


def test_english_date_format_does_not_use_chinese_date_suffix():
    view = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
    assert 'df.dateFormat = "MMM d \'at\' HH:mm"' in view
    assert 'return "Expires' in view


def test_full_reset_is_localized_only_at_the_ui_boundary():
    view = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
    backend_source = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
    assert '"完整重置"' in view
    assert 'item.get("title")' in backend_source


def test_no_changes_to_token_cost_quota_or_cli_schema_contracts():
    cli = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")
    assert "SCHEMA_VERSION = 1" in cli
    assert "reset_entitlements" in cli
