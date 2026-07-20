#!/usr/bin/env python3
"""One-time, atomic migration of QuotaView runtime data.

The installed app and CLI use Application Support.  This helper is invoked
only by the local install build when a project data directory is available;
the installed bundle never falls back to the source checkout.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_FILES = (
    "dashboard.json",
    "dashboard.json.bak",
    "daily_history.json",
    "daily_history.json.bak",
    "conversation_history.json",
    "conversation_history.json.bak",
    "settings.json",
    "settings.json.bak",
    "codex_scan_cache.json",
)


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _write_atomic(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _meaningful(name: str, value: dict) -> bool:
    if not value:
        return False
    if name.startswith("dashboard"):
        return bool(value.get("last_scan_time") or value.get("sources") or value.get("quota_status"))
    if name.startswith("settings"):
        return bool(value.get("model_prices") or value.get("language") or value.get("theme"))
    if name.startswith("daily_history"):
        return bool(value.get("days"))
    if name.startswith("conversation_history"):
        return bool(value.get("conversations"))
    if name.startswith("codex_scan_cache"):
        return bool(value.get("files") or value.get("sessions") or value)
    return True


def _union_preserving_target(name: str, source: dict, target: dict) -> dict:
    """Union disjoint records without adding duplicate usage totals."""
    result = copy.deepcopy(source)
    if name.startswith("daily_history"):
        result["days"] = copy.deepcopy(source.get("days", {}))
        result["days"].update(copy.deepcopy(target.get("days", {})))
        for key in ("seen_call_ids", "codex_seen_call_ids"):
            merged = dict(source.get(key, {}))
            merged.update(target.get(key, {}))
            if merged:
                result[key] = merged
    elif name.startswith("conversation_history"):
        merged = dict(source.get("conversations", {}))
        merged.update(target.get("conversations", {}))
        result["conversations"] = merged
    elif name.startswith("codex_scan_cache"):
        for key in ("files", "sessions"):
            merged = dict(source.get(key, {}))
            merged.update(target.get(key, {}))
            if merged:
                result[key] = merged
        result.update({key: value for key, value in target.items() if key not in {"files", "sessions"}})
    else:
        result.update(copy.deepcopy(target))
    return result


def migrate_runtime(source_dir: Path, target_dir: Path) -> dict:
    source_dir = Path(source_dir).expanduser().resolve()
    target_dir = Path(target_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target_dir, 0o700)
    report = {"source": str(source_dir), "target": str(target_dir), "copied": [], "merged": [], "kept": [], "skipped": []}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for name in RUNTIME_FILES:
        source = source_dir / name
        target = target_dir / name
        source_value = load_json(source) if source.exists() else None
        target_value = load_json(target) if target.exists() else None
        if source_value is None:
            report["skipped"].append(name)
            continue
        if target_value is None or not _meaningful(name, target_value):
            if target.exists():
                backup = target.with_name(f"{target.name}.migration-{stamp}.bak")
                backup.write_bytes(target.read_bytes())
                os.chmod(backup, 0o600)
            _write_atomic(target, source_value)
            report["copied"].append(name)
            continue
        merged = _union_preserving_target(name, source_value, target_value)
        if merged != target_value:
            _write_atomic(target, merged)
            report["merged"].append(name)
        else:
            report["kept"].append(name)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(migrate_runtime(args.source, args.target), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
