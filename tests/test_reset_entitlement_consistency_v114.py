import copy
import json
from pathlib import Path

import monitor_backend as backend
from cli import quotaview_cli as cli


OBSERVED = "2026-07-20T10:00:00Z"


def parse(credits, official_count=1):
    return backend.parse_reset_entitlements({"rateLimitResetCredits": {"availableCount": official_count, "credits": credits}}, OBSERVED)


def credit(**kwargs):
    row = {"id": "secret-entitlement-id", "resetType": "codexRateLimits", "title": "Full reset", "expiresAt": 1785528035}
    row.update(kwargs)
    return row


def test_available_count_and_list_are_derived_from_one_normalized_set():
    ent = parse([credit(status="AVAILABLE")], official_count=1)
    assert ent["available_count"] == len(ent["entitlements"]) == 1
    assert ent["count_list_consistent"] is True
    assert ent["entitlements"][0]["is_available"] is True


def test_mismatch_uses_normalized_count_for_display():
    ent = parse([credit(status="active"), credit(id="used", status="used")], official_count=3)
    assert ent["official_available_count"] == 3
    assert ent["available_count"] == len(ent["entitlements"]) == 1
    assert ent["count_list_consistent"] is False


def test_known_available_statuses_normalize_case_insensitively():
    ent = parse([credit(id=str(i), status=status) for i, status in enumerate(("AVAILABLE", "active", "ready", "enabled"))], official_count=4)
    assert ent["available_count"] == 4
    assert all(item["normalized_status"] == "available" for item in ent["entitlements"])


def test_missing_status_is_inferred_when_not_used_and_not_expired():
    ent = parse([credit(status=None, expiresAt=1785528035)], official_count=1)
    item = ent["entitlements"][0]
    assert item["is_available"] is True
    assert item["status_inferred"] is True
    assert ent["status_inferred_count"] == 1


def test_consumed_redeemed_revoked_and_cancelled_are_not_available():
    rows = [credit(id="consumed", status="available", consumed=True), credit(id="redeemed", status="redeemed"), credit(id="revoked", status="revoked"), credit(id="cancelled", status="cancelled")]
    ent = parse(rows, official_count=0)
    assert ent["available_count"] == 0
    assert all(not item["is_available"] for item in ent["items"])


def test_expired_status_is_not_available():
    ent = parse([credit(status="available", expiresAt=1)], official_count=0)
    assert ent["available_count"] == 0
    assert ent["items"][0]["normalized_status"] == "expired"


def test_expiration_supports_seconds_milliseconds_iso_rfc3339_and_date():
    rows = [
        credit(id="seconds", expiresAt=1785528035),
        credit(id="milliseconds", expiresAt=1785528035000),
        credit(id="iso", expiresAt="2026-08-13T01:38:00Z"),
        credit(id="rfc", expiresAt="2026-08-13T01:38:00+00:00"),
        credit(id="date", expiresAt=None, expiresOn="2026-08-13"),
    ]
    ent = parse(rows, official_count=5)
    assert ent["available_count"] == 5
    assert ent["expiration_parse_failures"] == 0
    assert ent["items"][-1]["expires_on"] == "2026-08-13"


def test_august_13_future_date_is_not_expired():
    ent = parse([credit(expiresAt="2026-08-13T01:38:00Z")], official_count=1)
    assert ent["entitlements"][0]["is_available"] is True


def test_stale_snapshot_recomputes_count_from_preserved_items():
    previous = parse([credit(status="available")], official_count=1)
    stale = backend._stale_reset(previous, "2026-07-20T10:01:00Z", "timeout")
    assert stale["status"] == "official_stale"
    assert stale["available_count"] == len(stale["entitlements"]) == 1
    assert stale["last_success_at"] == OBSERVED


def test_cli_returns_normalized_count_entitlements_and_consistency():
    reset = parse([credit(status="active")], official_count=1)
    dashboard = {"quota_status": {"codex": {"reset_entitlements": reset}}}
    out = cli.reset_data(dashboard)
    assert out["available_count"] == len(out["entitlements"]) == 1
    assert out["count_list_consistent"] is True
    assert out["official_available_count"] == 1
    assert out["status_inferred_count"] == 0


def test_cli_schema_remains_one_and_does_not_expose_entitlement_id():
    reset = parse([credit(status="available")], official_count=1)
    out = cli.reset_data({"quota_status": {"codex": {"reset_entitlements": reset}}})
    assert cli.SCHEMA_VERSION == 1
    assert "secret-entitlement-id" not in json.dumps(out)
    assert "id" not in out["entitlements"][0]


def test_swift_ui_uses_is_available_not_raw_status_for_rows_and_count():
    source = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
    block = source[source.index("// 2. Limit resets for Codex"):source.index("        .frame(maxWidth: .infinity", source.index("// 2. Limit resets for Codex"))]
    assert "ent.items.filter(\\.isAvailable)" in block
    assert "ent.availableCount ??" not in block
    assert 'status.lowercased() == "available"' not in block


def test_swift_model_decodes_normalized_entitlement_fields():
    source = Path("macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text(encoding="utf-8")
    assert "isAvailable =" in source
    assert "normalizedStatus" in source
    assert "statusInferred" in source


def test_no_reset_write_operations_added():
    source = Path("monitor_backend.py").read_text(encoding="utf-8")
    assert "redeem(" not in source.lower()
    assert "consume(" not in source.lower()
