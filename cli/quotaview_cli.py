#!/usr/bin/env python3
"""QuotaView's read-only command line interface.

This module intentionally contains presentation and validation only. Token,
cost, quota, and pricing calculations remain in the bundled backend and the
runtime dashboard/settings files are the sole data source.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 1
CLI_VERSION = "1.1.2"
APP_PATH = Path("/Applications/QuotaView.app")
BUNDLE_BACKEND = APP_PATH / "Contents/Resources/monitor_backend.py"
BUNDLE_CLI = APP_PATH / "Contents/Resources/quotaview_cli.py"
RUNTIME_DIR = Path(os.environ.get("TOKEN_MONITOR_DATA_DIR", str(Path.home() / "Library/Application Support/Antigravity Token Monitor")))

CURRENT_AG = ["claude-opus-4-6-thinking", "claude-sonnet-4-6", "gemini-3.5-flash", "gemini-3.1-pro", "gpt-oss-120b"]
CURRENT_CODEX = ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"]
LEGACY_CODEX = ["gpt-5.4", "gpt-5.4-mini"]


class CLIError(Exception):
    def __init__(self, code, message, exit_code=3):
        super().__init__(message)
        self.code, self.message, self.exit_code = code, message, exit_code


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def local_time(value):
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(text).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    except (TypeError, ValueError):
        return None


def load_json(name):
    path = RUNTIME_DIR / name
    if not path.exists():
        raise CLIError("runtime_missing", f"运行时文件不存在: {name}")
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise CLIError("invalid_json", f"无法读取 {name}: {exc}")


def envelope(command, payload=None, ok=True):
    result = {"schema_version": SCHEMA_VERSION, "command": command, "generated_at": now_iso(), "ok": ok}
    if payload:
        result.update(payload)
    return result


def source_names(source):
    if source == "all":
        return ["antigravity", "codex"]
    return [source]


def range_key(value):
    return {"today": "today", "7d": "last_7", "30d": "last_30", "all": "all_time"}[value]


def usage_data(source, period, dashboard):
    result = {}
    for name in source_names(source):
        src = dashboard.get("sources", {}).get(name)
        if not isinstance(src, dict):
            raise CLIError("runtime_missing", f"dashboard 缺少来源: {name}")
        row = src.get(period)
        if not isinstance(row, dict):
            raise CLIError("runtime_missing", f"dashboard 缺少范围: {name}.{period}")
        result[name] = {key: row.get(key, 0) for key in ("user_input_tokens", "output_tokens", "identifiable_tokens", "estimated_cost")}
    return result


def quota_data(source, dashboard):
    statuses = dashboard.get("quota_status", {})
    result = {}
    for name in source_names(source):
        status = statuses.get(name, {})
        items = []
        for item in status.get("items", []) if isinstance(status, dict) else []:
            if not isinstance(item, dict) or item.get("confidence") != "official_live":
                continue
            items.append({key: item.get(key) for key in ("name", "group", "window", "raw_percent", "used_percent", "percent_semantics", "reset_time", "observed_at", "source_path", "original_field_name", "plan_type", "plan_display_name", "plan_source", "plan_confidence") if key in item})
        result[name] = {"status": status.get("status", "unavailable"), "message": status.get("message", ""), "items": items}
        for key in ("plan_type", "plan_display_name", "plan_source", "plan_confidence", "plan_mismatch"):
            if key in status:
                result[name][key] = status[key]
    return result


def reset_data(dashboard):
    status = dashboard.get("quota_status", {}).get("codex", {}).get("reset_entitlements", {})
    items = []
    for item in status.get("items", []) if isinstance(status, dict) else []:
        if not isinstance(item, dict) or str(item.get("status", "")).lower() != "available":
            continue
        items.append({"display_name": item.get("display_name", ""), "status": "available", "expires_at": item.get("expires_at"), "expires_on": item.get("expires_on"), "display_time": local_time(item.get("expires_at"))})
    return {"status": status.get("status", "unavailable"), "available_count": status.get("available_count"), "count_semantics": status.get("count_semantics"), "source_path": status.get("source_path"), "observed_at": status.get("observed_at"), "items": items}


def prices_data(source, settings, include_legacy):
    prices = settings.get("model_prices", {})
    ids = []
    if source in ("all", "antigravity"):
        ids.extend(CURRENT_AG)
    if source in ("all", "codex"):
        ids.extend(CURRENT_CODEX)
        if include_legacy:
            ids.extend(LEGACY_CODEX)
    output = []
    for model_id in ids:
        p = prices.get(model_id, {})
        row = {"raw_model_id": model_id, "display_name": p.get("display_name", model_id), "user_overridden": bool(p.get("user_overridden", False)), "pricing_profile": p.get("pricing_profile"), "pricing_source": p.get("pricing_source"), "pricing_verified_at": p.get("pricing_verified_at"), "tiered_pricing": {"threshold_tokens": p.get("threshold_tokens"), "standard": p.get("standard"), "long_context": p.get("long_context")} if p.get("threshold_tokens") else None, "unpriced": p.get("pricing_profile") == "unpriced" or (not p.get("input_price_per_million") and not p.get("output_price_per_million"))}
        if row["unpriced"]:
            row["display_price"] = "未定价"
            if model_id == "gpt-oss-120b":
                row["unpriced_status"] = "open_weight_no_unified_api_price"
                row["unpriced_reason"] = "开放权重；无统一 API 单价，运行成本取决于托管平台或本地算力"
        else:
            row["input_price_per_million"] = p.get("input_price_per_million", 0)
            row["cached_input_price_per_million"] = p.get("cached_input_price_per_million", 0)
            row["output_price_per_million"] = p.get("output_price_per_million", 0)
        output.append(row)
    return output


def resolved_pricing_data(source, dashboard, settings):
    """Read-only audit of the prices actually resolved for today's models."""
    prices = settings.get("model_prices", {})
    rows = []
    for name in source_names(source):
        today = dashboard.get("sources", {}).get(name, {}).get("today", {})
        for model_id, metrics in (today.get("models", {}) or {}).items():
            canonical = "gemini-3-flash-a" if model_id == "gemini-default" else model_id
            price = prices.get(canonical, {})
            inp = int(metrics.get("user_input_tokens", 0))
            cached = int(metrics.get("cached_input_tokens", 0))
            out = int(metrics.get("output_tokens", 0))
            unpriced = price.get("pricing_profile") == "unpriced" or (not price.get("input_price_per_million") and not price.get("output_price_per_million"))
            rows.append({
                "source": name,
                "raw_model_id": model_id,
                "normalized_model_id": canonical,
                "display_name": price.get("display_name", model_id),
                "input_tokens": inp,
                "cached_input_tokens": cached,
                "output_tokens": out,
                "pricing_profile": price.get("pricing_profile"),
                "input_price_per_million": price.get("input_price_per_million", 0) if not unpriced else None,
                "cached_input_price_per_million": price.get("cached_input_price_per_million", 0) if not unpriced else None,
                "output_price_per_million": price.get("output_price_per_million", 0) if not unpriced else None,
                "calculated_cost": metrics.get("estimated_cost", 0.0),
                "unpriced": unpriced,
                "pricing_source": price.get("pricing_source"),
                "pricing_breakdown": metrics.get("pricing_breakdown")
            })
    return rows


def status_data(dashboard):
    today = usage_data("all", "today", dashboard)
    quota = quota_data("all", dashboard)
    reset = reset_data(dashboard)
    return {"sources": {name: {"today": today[name], "official_live": quota[name]} for name in today}, "codex_resets": reset, "dashboard_updated_at": dashboard.get("last_scan_time"), "dashboard_display_time": local_time(dashboard.get("last_scan_time"))}


def print_json(value):
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def print_usage(source, period, data):
    print(f"QuotaView 使用量 · {source} · {period}")
    for name, row in data.items():
        print(f"{name}: 输入 {int(row['user_input_tokens']):,} · 输出 {int(row['output_tokens']):,} · 可识别 {int(row['identifiable_tokens']):,} · 成本 {row['estimated_cost']}")


def print_quota(source, data):
    for name, value in data.items():
        print(f"{name}: {value['status']}")
        for item in value["items"]:
            print(f"  {item.get('name', '')}: used {item.get('used_percent')}% · reset {item.get('reset_time')}")


def refresh(args):
    if not BUNDLE_BACKEND.exists():
        raise CLIError("app_missing", "App Bundle 内缺少 monitor_backend.py")
    env = dict(os.environ, TOKEN_MONITOR_DATA_DIR=str(RUNTIME_DIR))
    if args.wait:
        env["TOKEN_MONITOR_WAIT_FOR_LOCK"] = "1"
        env["TOKEN_MONITOR_LOCK_TIMEOUT"] = str(args.timeout)
    else:
        env["TOKEN_MONITOR_WAIT_FOR_LOCK"] = "0"
    try:
        proc = subprocess.run(["/usr/bin/env", "python3", str(BUNDLE_BACKEND)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=args.timeout + 5)
    except subprocess.TimeoutExpired:
        raise CLIError("scan_timeout", "QuotaView 扫描超时", 75)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if proc.returncode == 75:
        raise CLIError("scan_busy", "QuotaView 扫描正在运行", 75)
    if proc.returncode != 0:
        raise CLIError("scan_failed", "QuotaView 扫描失败", 3)
    dashboard = load_json("dashboard.json")
    payload = {"refresh_completed_at": now_iso(), "dashboard_updated_at": dashboard.get("last_scan_time"), "summary": status_data(dashboard)}
    return payload


def doctor_data():
    lock = RUNTIME_DIR / "scan.lock"
    ps = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout.splitlines()
    backend_processes = [line.strip() for line in ps if "monitor_backend.py" in line and "quotaview_cli.py" not in line]
    dashboard_ok = settings_ok = False
    try:
        load_json("dashboard.json"); dashboard_ok = True
    except CLIError: pass
    try:
        load_json("settings.json"); settings_ok = True
    except CLIError: pass
    return {"app_bundle": {"path": str(APP_PATH), "exists": APP_PATH.exists()}, "resources": {"monitor_backend": BUNDLE_BACKEND.exists(), "cli": BUNDLE_CLI.exists()}, "global_command": {"path": shutil.which("quotaview")}, "runtime": {"path": str(RUNTIME_DIR), "exists": RUNTIME_DIR.exists(), "readable": os.access(RUNTIME_DIR, os.R_OK), "writable": os.access(RUNTIME_DIR, os.W_OK), "dashboard_valid": dashboard_ok, "settings_valid": settings_ok}, "official_live": quota_data("all", load_json("dashboard.json")) if dashboard_ok else {}, "codex_reset_entitlements": reset_data(load_json("dashboard.json")) if dashboard_ok else {}, "cli_version": CLI_VERSION, "scan_lock": {"path": str(lock), "exists": lock.exists()}, "monitor_backend_processes": backend_processes, "abnormal_residual_scan_processes": []}


def build_parser():
    parser = argparse.ArgumentParser(prog="quotaview", description="QuotaView 只读数据查询工具")
    parser.add_argument("--version", action="version", version=CLI_VERSION)
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("status", help="显示 Antigravity 与 Codex 总览"); p.add_argument("--json", action="store_true")
    p = subs.add_parser("usage", help="读取 Token 使用量"); p.add_argument("source", nargs="?", choices=["all", "antigravity", "codex"], default="all"); p.add_argument("--range", choices=["today", "7d", "30d", "all"], default="today"); p.add_argument("--json", action="store_true")
    p = subs.add_parser("quota", help="读取 official_live 额度"); p.add_argument("source", nargs="?", choices=["all", "antigravity", "codex"], default="all"); p.add_argument("--json", action="store_true")
    p = subs.add_parser("resets", help="读取 Codex 可用重置权益"); p.add_argument("--json", action="store_true")
    p = subs.add_parser("prices", help="读取运行时模型价格"); p.add_argument("source", nargs="?", choices=["all", "antigravity", "codex"], default="all"); p.add_argument("--source", dest="source_option", choices=["all", "antigravity", "codex"]); p.add_argument("--include-legacy", action="store_true"); p.add_argument("--resolved", action="store_true"); p.add_argument("--json", action="store_true")
    p = subs.add_parser("refresh", help="调用 App Bundle 后端刷新数据"); p.add_argument("--wait", action="store_true"); p.add_argument("--timeout", type=float, default=90); p.add_argument("--json", action="store_true")
    p = subs.add_parser("doctor", help="检查本地安装与运行时数据"); p.add_argument("--json", action="store_true")
    subs.add_parser("version", help="显示 CLI 版本")
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "version":
            print(CLI_VERSION); return 0
        if args.command == "status":
            result = envelope("status", status_data(load_json("dashboard.json")))
            if args.json: print_json(result)
            else:
                for name, value in result["sources"].items():
                    today = value["today"]
                    print(f"{name}: 输入 {today['user_input_tokens']:,} · 输出 {today['output_tokens']:,} · 可识别 {today['identifiable_tokens']:,} · 成本 {today['estimated_cost']} · official_live {value['official_live']['status']}")
                print(f"Codex 可用重置次数: {result['codex_resets'].get('available_count')}")
                print(f"dashboard 更新时间: {result['dashboard_updated_at']} ({result['dashboard_display_time']})")
        elif args.command == "usage":
            period = range_key(args.range); data = usage_data(args.source, period, load_json("dashboard.json")); result = envelope("usage", {"source": args.source, "range": args.range, "usage": data})
            if args.json: print_json(result)
            else: print_usage(args.source, args.range, data)
        elif args.command == "quota":
            result = envelope("quota", {"source": args.source, "quota": quota_data(args.source, load_json("dashboard.json"))})
            if args.json: print_json(result)
            else: print_quota(args.source, result["quota"])
        elif args.command == "resets":
            result = envelope("resets", {"resets": reset_data(load_json("dashboard.json"))})
            if args.json: print_json(result)
            else: print(json.dumps(result["resets"], ensure_ascii=False, indent=2))
        elif args.command == "prices":
            price_source = args.source_option or args.source
            settings = load_json("settings.json")
            dashboard = load_json("dashboard.json")
            result = envelope("prices", {"source": price_source, "include_legacy": args.include_legacy, "resolved": args.resolved, "prices": resolved_pricing_data(price_source, dashboard, settings) if args.resolved else prices_data(price_source, settings, args.include_legacy)})
            if args.json: print_json(result)
            else:
                for item in result["prices"]:
                    if args.resolved:
                        print(f"{item['raw_model_id']} → {item['normalized_model_id']}: {item['input_tokens']:,} input · {item['output_tokens']:,} output · cost {item['calculated_cost']} · {item['pricing_profile']}")
                    else:
                        print(f"{item['display_name']}: {item.get('display_price', item.get('input_price_per_million'))}")
        elif args.command == "refresh":
            result = envelope("refresh", refresh(args));
            if args.json: print_json(result)
            else: print(f"刷新完成 · dashboard {result['dashboard_updated_at']}")
        elif args.command == "doctor":
            result = envelope("doctor", doctor_data())
            if args.json: print_json(result)
            else: print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except CLIError as exc:
        error = envelope(getattr(args, "command", "unknown"), {"error": {"code": exc.code, "message": exc.message}}, ok=False)
        print_json(error)
        return exc.exit_code
    except (KeyError, TypeError, ValueError) as exc:
        print_json(envelope(getattr(locals().get("args", None), "command", "unknown"), {"error": {"code": "invalid_runtime_data", "message": str(exc)}}, ok=False))
        return 3


if __name__ == "__main__":
    sys.exit(main())
