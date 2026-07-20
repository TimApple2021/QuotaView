import json
import os
from pathlib import Path

import runtime_migration as migration


ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_missing_application_support_is_created_and_migrated(tmp_path):
    source = tmp_path / "data"
    target = tmp_path / "Library" / "Application Support" / "Antigravity Token Monitor"
    source.mkdir()
    write_json(source / "dashboard.json", {"last_scan_time": "T1", "sources": {"codex": {}}})
    write_json(source / "settings.json", {"language": "English"})

    report = migration.migrate_runtime(source, target)

    assert target.is_dir()
    assert (target / "dashboard.json").exists()
    assert (target / "settings.json").exists()
    assert report["copied"] == ["dashboard.json", "settings.json"]
    assert oct(target.stat().st_mode & 0o777) == "0o700"
    assert json.loads((target / "dashboard.json").read_text())["last_scan_time"] == "T1"


def test_valid_target_is_not_overwritten_and_disjoint_history_is_union(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir(); target.mkdir()
    write_json(source / "settings.json", {"language": "English", "theme": "dark"})
    write_json(target / "settings.json", {"language": "中文", "theme": "light"})
    write_json(source / "daily_history.json", {"version": 4, "days": {"2026-01-01": {}}})
    write_json(target / "daily_history.json", {"version": 4, "days": {"2026-01-02": {}}})

    report = migration.migrate_runtime(source, target)

    assert "settings.json" in report["kept"]
    assert "daily_history.json" in report["merged"]
    assert json.loads((target / "settings.json").read_text())["language"] == "中文"
    assert set(json.loads((target / "daily_history.json").read_text())["days"]) == {"2026-01-01", "2026-01-02"}


def test_corrupt_source_is_not_migrated_and_corrupt_target_is_backed_up(tmp_path):
    source = tmp_path / "source"; target = tmp_path / "target"
    source.mkdir(); target.mkdir()
    (source / "dashboard.json").write_text("{", encoding="utf-8")
    (target / "dashboard.json").write_text("{", encoding="utf-8")
    write_json(source / "settings.json", {"language": "English"})
    (target / "settings.json").write_text("{", encoding="utf-8")

    report = migration.migrate_runtime(source, target)

    assert "dashboard.json" in report["skipped"]
    assert "settings.json" in report["copied"]
    assert list(target.glob("settings.json.migration-*.bak"))
    assert json.loads((target / "settings.json").read_text())["language"] == "English"


def test_atomic_writer_leaves_valid_json_and_secure_file(tmp_path):
    path = tmp_path / "settings.json"
    migration._write_atomic(path, {"language": "English"})
    assert json.loads(path.read_text())["language"] == "English"
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert not list(tmp_path.glob("*.tmp"))


def test_production_path_contract_is_explicit_and_shared():
    cli = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")
    scanner = (ROOT / "macos/AntigravityTokenMonitor/ScannerRunner.swift").read_text(encoding="utf-8")
    reader = (ROOT / "macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text(encoding="utf-8")
    build = (ROOT / "macos/build.sh").read_text(encoding="utf-8")
    assert "Library/Application Support/Antigravity Token Monitor" in cli
    assert "TokenRuntimePaths.appSupportDirectory.path" in scanner
    assert 'appendingPathComponent("Antigravity Token Monitor"' in reader
    assert "runtime_migration.py" in build


def test_release_backup_directories_have_no_executable_app_bundles():
    backup = ROOT / "data/backup"
    assert not list(backup.rglob("*.app"))


def test_cli_schema_and_backend_test_override_remain_available():
    cli = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")
    backend = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
    assert "SCHEMA_VERSION = 1" in cli
    assert "TOKEN_MONITOR_DATA_DIR" in cli
    assert "TOKEN_MONITOR_DATA_DIR" in backend
