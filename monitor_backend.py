import os
import json
import re
import time
import hashlib
import subprocess
import select
import shutil
import sys
import fcntl
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Default configuration settings in Chinese
DEFAULT_SETTINGS = {
    "app_data_dirs": [
        os.path.expanduser("~/.gemini/antigravity"),
        os.path.expanduser("~/.gemini/antigravity-cli")
    ],
    "system_prompt_tokens": 0,  # 默认值为0，代表用户没有设置系统上下文假设值时为0
    "pricing_tier": "standard",  # standard or priority
    "model_prices": {
        "gemini-3-flash-a": {
            "display_name": "Gemini 3.5 Flash",
            "provider": "Google",
            "input_price_per_million": 1.50,
            "output_price_per_million": 9.00,
            "cached_input_price_per_million": 0.15,
            "pricing_profile": "api_standard_equivalent",
            "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_billing_confirmed": False
        },
        "gemini-3.5-flash": {
            "display_name": "Gemini 3.5 Flash",
            "provider": "Google",
            "input_price_per_million": 1.50,
            "output_price_per_million": 9.00,
            "cached_input_price_per_million": 0.15,
            "pricing_profile": "api_standard_equivalent",
            "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_billing_confirmed": False,
            "raw_model_id": "gemini-3.5-flash"
        },
        "gemini-3.1-pro": {
            "display_name": "Gemini 3.1 Pro",
            "provider": "Google",
            "input_price_per_million": 2.00,
            "output_price_per_million": 12.00,
            "cached_input_price_per_million": 0.20,
            "threshold_tokens": 200000,
            "standard": {"input": 2.00, "cached": 0.20, "output": 12.00},
            "long_context": {"input": 4.00, "cached": 0.40, "output": 18.00},
            "standard_input_price": 2.00,
            "standard_cached_input_price": 0.20,
            "standard_output_price": 12.00,
            "long_context_input_price": 4.00,
            "long_context_cached_input_price": 0.40,
            "long_context_output_price": 18.00,
            "pricing_profile": "api_standard_equivalent_tiered",
            "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_billing_confirmed": False,
            "raw_model_id": "gemini-3.1-pro"
        },
        "gpt-oss-120b": {
            "display_name": "GPT-OSS 120B",
            "provider": "OpenAI / Antigravity hosted",
            "input_price_per_million": 0.0,
            "output_price_per_million": 0.0,
            "cached_input_price_per_million": 0.0,
            "pricing_profile": "unpriced",
            "pricing_source": "provider_specific",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_billing_confirmed": False,
            "raw_model_id": "gpt-oss-120b"
        },
        "claude-sonnet-4-6": {
            "display_name": "Claude Sonnet 4.6",
            "provider": "Anthropic",
            "input_price_per_million": 3.00,
            "output_price_per_million": 15.00,
            "pricing_profile": "api_standard_equivalent",
            "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_billing_confirmed": False
        },
        "claude-opus-4-6-thinking": {
            "display_name": "Claude Opus 4.6",
            "provider": "Anthropic",
            "input_price_per_million": 5.00,
            "output_price_per_million": 25.00,
            "pricing_profile": "api_standard_equivalent",
            "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_billing_confirmed": False
        },
        "gpt-5.6-luna": {
            "display_name": "GPT-5.6 Luna",
            "provider": "OpenAI",
            "input_price_per_million": 1.00,
            "cached_input_price_per_million": 0.10,
            "output_price_per_million": 6.00,
            "pricing_unit": "credits",
            "pricing_profile": "api_standard_equivalent",
            "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_extra_charge_confirmed": False,
            "raw_model_id": "gpt-5.6-luna"
        },
        "gpt-5.6-sol": {
            "display_name": "GPT-5.6 Sol", "provider": "OpenAI",
            "input_price_per_million": 5.00, "cached_input_price_per_million": 0.50,
            "output_price_per_million": 30.00, "pricing_unit": "credits",
            "pricing_profile": "api_standard_equivalent", "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17", "user_overridden": False,
            "actual_extra_charge_confirmed": False, "raw_model_id": "gpt-5.6-sol"
        },
        "gpt-5.6-terra": {
            "display_name": "GPT-5.6 Terra", "provider": "OpenAI",
            "input_price_per_million": 2.50, "cached_input_price_per_million": 0.25,
            "output_price_per_million": 15.00, "pricing_unit": "credits",
            "pricing_profile": "api_standard_equivalent", "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17", "user_overridden": False,
            "actual_extra_charge_confirmed": False, "raw_model_id": "gpt-5.6-terra"
        },
        "gpt-5.5": {
            "display_name": "GPT-5.5", "provider": "OpenAI",
            "input_price_per_million": 5.00, "cached_input_price_per_million": 0.50,
            "output_price_per_million": 30.00, "pricing_unit": "credits",
            "pricing_profile": "api_standard_equivalent", "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17", "user_overridden": False,
            "actual_extra_charge_confirmed": False, "raw_model_id": "gpt-5.5"
        },
        "gpt-5.4": {
            "display_name": "GPT-5.4", "provider": "OpenAI",
            "input_price_per_million": 2.50, "cached_input_price_per_million": 0.25,
            "output_price_per_million": 15.00, "pricing_unit": "credits",
            "pricing_profile": "api_standard_equivalent", "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17", "user_overridden": False,
            "actual_extra_charge_confirmed": False, "raw_model_id": "gpt-5.4"
        },
        "gpt-5.4-mini": {
            "display_name": "GPT-5.4 Mini", "provider": "OpenAI",
            "input_price_per_million": 0.75, "cached_input_price_per_million": 0.075,
            "output_price_per_million": 4.50, "pricing_unit": "credits",
            "pricing_profile": "api_standard_equivalent", "pricing_source": "official_public_api",
            "pricing_verified_at": "2026-07-17", "user_overridden": False,
            "actual_extra_charge_confirmed": False, "raw_model_id": "gpt-5.4-mini"
        },
        "codex-auto-review": {
            "display_name": "Codex Auto Review",
            "provider": "OpenAI",
            "input_price_per_million": 0.0,
            "cached_input_price_per_million": 0.0,
            "output_price_per_million": 0.0,
            "pricing_unit": "credits",
            "pricing_profile": "unmapped",
            "pricing_source": "unmapped",
            "pricing_verified_at": "2026-07-17",
            "user_overridden": False,
            "actual_extra_charge_confirmed": False,
            "raw_model_id": "codex-auto-review"
        }
    }
}

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.environ.get("TOKEN_MONITOR_DATA_DIR", os.path.join(PROJECT_ROOT, "data")))
os.makedirs(DATA_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
CACHE_FILE = os.path.join(DATA_DIR, "codex_scan_cache.json")
LAST_SCAN_METADATA = {"codex_calls": [], "codex_auth_info": {"auth_mode": "Unknown", "plan_type": "unknown_plan"}, "scanner_stats": {}}
SCAN_LOCK_FILE = os.path.join(DATA_DIR, "scan.lock")


class ScanBusyError(RuntimeError):
    """Raised when another GUI/CLI scanner owns the shared scan lock."""


@contextmanager
def scan_lock():
    """Serialize every scan process, including GUI-launched backend processes."""
    os.makedirs(DATA_DIR, exist_ok=True)
    wait = os.environ.get("TOKEN_MONITOR_WAIT_FOR_LOCK", "0") == "1"
    try:
        timeout = max(float(os.environ.get("TOKEN_MONITOR_LOCK_TIMEOUT", "90")), 0.0)
    except ValueError:
        timeout = 90.0
    started = time.monotonic()
    handle = open(SCAN_LOCK_FILE, "a+", encoding="utf-8")
    try:
        while True:
            try:
                flags = fcntl.LOCK_EX
                if not wait:
                    flags |= fcntl.LOCK_NB
                fcntl.flock(handle.fileno(), flags)
                handle.seek(0)
                handle.truncate()
                handle.write(f"pid={os.getpid()}\n")
                handle.flush()
                break
            except BlockingIOError:
                if not wait or time.monotonic() - started >= timeout:
                    raise ScanBusyError("QuotaView 扫描正在运行")
                time.sleep(0.1)
        yield handle
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

ANTIGRAVITY_CURRENT_MODEL_ORDER = [
    "claude-opus-4-6-thinking", "claude-sonnet-4-6", "gemini-3.5-flash",
    "gemini-3.1-pro", "gpt-oss-120b"
]
CODEX_CURRENT_MODEL_ORDER = ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5"]

def normalize_antigravity_model(model_id):
    """Normalize provider display variants without changing legacy ledger IDs."""
    value = str(model_id or "").strip().lower()
    if value in {"gemini-3.5-flash", "gemini-3.5-flash-low", "gemini-3.5-flash-medium", "gemini-3.5-flash-high",
                 "gemini 3.5 flash", "gemini 3.5 flash (low)", "gemini 3.5 flash (medium)", "gemini 3.5 flash (high)"}:
        return "gemini-3.5-flash"
    if value in {"gemini-3.1-pro", "gemini-3.1-pro-low", "gemini-3.1-pro-high",
                 "gemini 3.1 pro", "gemini 3.1 pro (low)", "gemini 3.1 pro (high)"}:
        return "gemini-3.1-pro"
    if value in {"claude-sonnet-4-6", "claude sonnet 4.6", "claude sonnet 4.6 (thinking)"}:
        return "claude-sonnet-4-6"
    if value in {"claude-opus-4-6-thinking", "claude opus 4.6", "claude opus 4.6 (thinking)"}:
        return "claude-opus-4-6-thinking"
    if value in {"gpt-oss-120b", "gpt-oss 120b", "gpt-oss 120b (medium)"}:
        return "gpt-oss-120b"
    # Preserve the accepted historical key so existing totals do not move.
    if value in {"gemini-3-flash-a", "gemini-3-flash-agent", "gemini-default"}:
        return "gemini-3-flash-a"
    return str(model_id or "unknown_legacy")


def pricing_model_id(model_id):
    """Resolve legacy/internal Antigravity IDs to their priced canonical ID."""
    if str(model_id or "").strip().lower() == "gemini-default":
        return "gemini-3-flash-a"
    return model_id

def pricing_rates_for_model(model_id, input_tokens, model_prices):
    """Return (input, cached, output) rates using the request's input size."""
    model_id = pricing_model_id(model_id)
    p = model_prices.get(model_id, {}) if isinstance(model_prices, dict) else {}
    if model_id == "gemini-3.1-pro" and isinstance(p.get("standard"), dict):
        threshold = int(p.get("threshold_tokens", 200000))
        tier = p["standard"] if int(input_tokens or 0) <= threshold else p.get("long_context", p["standard"])
        return (float(tier.get("input", 0.0)), float(tier.get("cached", 0.0)), float(tier.get("output", 0.0)))
    return (float(p.get("input_price_per_million", 0.0)),
            float(p.get("cached_input_price_per_million", 0.0)),
            float(p.get("output_price_per_million", 0.0)))

def cost_for_call(model_id, input_tokens, cached_tokens, output_tokens, model_prices):
    in_rate, cached_rate, out_rate = pricing_rates_for_model(model_id, input_tokens, model_prices)
    return (Decimal(max(int(input_tokens or 0) - int(cached_tokens or 0), 0)) * Decimal(str(in_rate)) /
            Decimal("1000000") + Decimal(int(cached_tokens or 0)) * Decimal(str(cached_rate)) /
            Decimal("1000000") + Decimal(int(output_tokens or 0)) * Decimal(str(out_rate)) /
            Decimal("1000000"))


def is_priced_model(model_id, model_prices):
    p = model_prices.get(pricing_model_id(model_id), {}) if isinstance(model_prices, dict) else {}
    return p.get("pricing_profile") == "codex_official_credit_rate" or (
        p.get("input_price_per_million", 0) > 0 and p.get("output_price_per_million", 0) > 0
    )

def dynamic_model_options(summary, model_prices):
    """Return the UI model menu for one source/range summary."""
    models = summary.get("models", {}) if isinstance(summary, dict) else {}
    used = [(mid, item) for mid, item in models.items()
            if item.get("identifiable_tokens", item.get("user_input_tokens", 0) + item.get("output_tokens", 0)) > 0
            or item.get("call_count", 0) > 0]
    used.sort(key=lambda pair: (-pair[1].get("identifiable_tokens", 0), pair[0]))
    options = ["all"] + [mid for mid, _ in used]
    if any(mid == "missing_model" for mid, _ in used): options.append("missing_model")
    return options

def settings_model_ids(source_key, model_prices, daily_history, dashboard_sources):
    """Build the settings catalog from cumulative sources, never a range summary."""
    ids = set()
    for day in (daily_history or {}).get("days", []):
        ids.update((((day.get("sources") or {}).get(source_key) or {}).get("models") or {}).keys())
    source = (dashboard_sources or {}).get(source_key) or {}
    ids.update((((source.get("all_time") or {}).get("models") or {}).keys()))
    if source_key == "codex":
        # The client selector is the authoritative current list. Legacy prices
        # remain in settings for historical cost calculation but stay hidden.
        return list(CODEX_CURRENT_MODEL_ORDER)
    ordered = []
    for model_id in ANTIGRAVITY_CURRENT_MODEL_ORDER:
        if model_id not in ordered:
            ordered.append(model_id)
    for model_id in sorted(ids):
        if model_id in {"unknown_legacy", "gemini-default", "gemini-3-flash-a", "codex-auto-review"}:
            continue
        if model_id not in ordered:
            ordered.append(model_id)
    return ordered

def credits_display_state(summary, model_prices):
    """Return (text, note) for the Credits card without confusing unpriced with zero."""
    models = summary.get("models", {}) if isinstance(summary, dict) else {}
    total = sum(m.get("identifiable_tokens", m.get("user_input_tokens", 0) + m.get("output_tokens", 0)) for m in models.values())
    unpriced = 0
    credits = Decimal("0")
    for mid, m in models.items():
        tokens = m.get("identifiable_tokens", m.get("user_input_tokens", 0) + m.get("output_tokens", 0))
        p = model_prices.get(pricing_model_id(mid), {})
        configured = is_priced_model(mid, model_prices)
        if mid != "missing_model" and not configured: unpriced += tokens
        if configured:
            inp, cached, out = m.get("user_input_tokens", 0), m.get("cached_input_tokens", 0), m.get("output_tokens", 0)
            credits += Decimal(max(inp - cached, 0)) * Decimal(str(p.get("input_price_per_million", 0))) / Decimal("1000000")
            credits += Decimal(cached) * Decimal(str(p.get("cached_input_price_per_million", 0))) / Decimal("1000000")
            credits += Decimal(out) * Decimal(str(p.get("output_price_per_million", 0))) / Decimal("1000000")
    if total == 0: return "0.0000 Credits", "当前范围暂无可统计数据"
    if unpriced >= total: return "未计算", "当前模型尚未配置官方 Credits 费率"
    note = f"另有 {unpriced} Token 未配置费率" if unpriced else None
    return f"{credits:.4f} Credits", note

def load_settings():
    import copy
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                
                # Make sure pricing_tier defaults to "standard"
                tier = loaded.get("pricing_tier", "standard")
                
                merged = copy.deepcopy(DEFAULT_SETTINGS)
                merged.update(loaded)
                merged["pricing_tier"] = tier
                
                # Merge model_prices
                if "model_prices" in loaded:
                    prices = copy.deepcopy(DEFAULT_SETTINGS["model_prices"])
                    for model_id, loaded_info in loaded["model_prices"].items():
                        if isinstance(loaded_info, dict) and isinstance(prices.get(model_id), dict):
                            prices[model_id].update(loaded_info)
                        else:
                            prices[model_id] = loaded_info
                    merged["model_prices"] = prices
                    new_model_defaults_added = (
                        any(k not in loaded["model_prices"] for k in (
                            "gemini-3.5-flash", "gemini-3.1-pro", "gpt-oss-120b", "gpt-5.6-terra", "gpt-5.5")) or
                        any(k not in loaded["model_prices"].get("gemini-3.1-pro", {}) for k in (
                            "threshold_tokens", "standard", "long_context"))
                    )
                else:
                    merged["model_prices"] = copy.deepcopy(DEFAULT_SETTINGS["model_prices"])
                    new_model_defaults_added = True
                
                # Migrate 25x errors for Codex models when user_overridden == false
                corrections = {
                    "gpt-5.4": {"input": 2.50, "cached": 0.25, "output": 15.00, "error_inputs": [62.5], "error_outputs": [375.0]},
                    "gpt-5.4-mini": {"input": 0.75, "cached": 0.075, "output": 4.50, "error_inputs": [18.75], "error_outputs": [112.5, 113.0]},
                    "gpt-5.6-luna": {"input": 1.00, "cached": 0.10, "output": 6.00, "error_inputs": [25.0], "error_outputs": [150.0]},
                    "gpt-5.6-sol": {"input": 5.00, "cached": 0.50, "output": 30.00, "error_inputs": [125.0], "error_outputs": [750.0]},
                    "gpt-5.6-terra": {"input": 2.50, "cached": 0.25, "output": 15.00, "error_inputs": [62.5], "error_outputs": [375.0]},
                    "gpt-5.5": {"input": 5.00, "cached": 0.50, "output": 30.00, "error_inputs": [125.0], "error_outputs": [750.0]}
                }
                
                migrated = False
                for model_id, target in corrections.items():
                    if model_id in merged["model_prices"]:
                        model_info = merged["model_prices"][model_id]
                        if isinstance(model_info, dict):
                            current_in = model_info.get("input_price_per_million", 0.0)
                            current_out = model_info.get("output_price_per_million", 0.0)
                            is_error = False
                            for err_in in target["error_inputs"]:
                                if abs(current_in - err_in) < 1e-2:
                                    is_error = True
                            for err_out in target["error_outputs"]:
                                if abs(current_out - err_out) < 1e-2:
                                    is_error = True
                            if is_error:
                                if not model_info.get("user_overridden", False):
                                    model_info["input_price_per_million"] = target["input"]
                                    model_info["cached_input_price_per_million"] = target["cached"]
                                    model_info["output_price_per_million"] = target["output"]
                                    model_info["pricing_profile"] = "api_standard_equivalent"
                                    model_info["pricing_source"] = "official_public_api"
                                    migrated = True
                                    
                if migrated:
                    import sys
                    print("检测到未迁移的 Codex 25倍错误价格，正在自动迁移并原子写回 settings.json...", file=sys.stderr)
                    save_settings(merged)

                if new_model_defaults_added:
                    # Add only missing defaults; loaded user_overridden values remain intact.
                    save_settings(merged)
                
                # Dynamic update of gemini-3-flash-a based on pricing_tier when not overridden
                gem = merged["model_prices"].get("gemini-3-flash-a")
                if isinstance(gem, dict) and not gem.get("user_overridden", False):
                    if tier == "priority":
                        gem["input_price_per_million"] = 2.70
                        gem["output_price_per_million"] = 16.20
                        gem["cached_input_price_per_million"] = 0.27
                    else:
                        gem["input_price_per_million"] = 1.50
                        gem["output_price_per_million"] = 9.00
                        gem["cached_input_price_per_million"] = 0.15
                
                return merged
        except Exception as e:
            import sys
            print(f"读取 settings.json 异常，返回默认值: {e}", file=sys.stderr)
            return copy.deepcopy(DEFAULT_SETTINGS)
    return copy.deepcopy(DEFAULT_SETTINGS)

def save_settings(settings):
    try:
        import sys
        # Create backup first
        backup_path = SETTINGS_FILE + ".bak"
        if os.path.exists(SETTINGS_FILE):
            import shutil
            try:
                shutil.copy2(SETTINGS_FILE, backup_path)
            except Exception as e:
                print(f"备份 settings.json 失败: {e}", file=sys.stderr)
        
        # Write to temp file in the same directory
        temp_path = SETTINGS_FILE + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
            
        # Atomic replace
        os.replace(temp_path, SETTINGS_FILE)
        return True
    except Exception as e:
        import sys
        print(f"原子写入 settings.json 失败: {e}", file=sys.stderr)
        return False

def estimate_tokens(text: str) -> int:
    """
    Estimates token count of a string.
    - CJK characters: ~1.3 tokens each (based on Gemini tokenization).
    - English and code characters: ~0.27 tokens each (approx 3.7 characters per token).
    """
    if not text:
        return 0
    cjk_count = 0
    other_chars = 0
    for char in text:
        val = ord(char)
        # CJK Unified Ideographs, Extension A, and Compatibility Ideographs
        if 0x4E00 <= val <= 0x9FFF or 0x3400 <= val <= 0x4DBF or 0xF900 <= val <= 0xFAFF:
            cjk_count += 1
        else:
            other_chars += 1
    
    tokens = int(cjk_count * 1.3 + other_chars * 0.27)
    return max(1, tokens)

def get_file_hash(file_path: str) -> str:
    """Computes MD5 hash of a file for change tracking."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return ""

def to_local_date(iso_str: str) -> str:
    """
    Converts a UTC ISO-8601 string to a local natural day date (YYYY-MM-DD).
    Falls back to parsing and timezone conversion or string split.
    """
    if not iso_str:
        return "未知"
    try:
        # Convert Z suffix to +00:00 to support fromisoformat in standard python
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1] + '+00:00'
        dt = datetime.fromisoformat(iso_str)
        # astimezone() with no args converts to the local system time zone
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d")
    except Exception:
        # Simple fallback split
        try:
            return iso_str.split("T")[0]
        except Exception:
            return "未知"

def classify_tokens(step: dict):
    """
    Classifies content of a step into different categories and returns token counts.
    """
    cats = {
        "user_input": 0,
        "assistant_output": 0,
        "tool_calls": 0,
        "tool_returns": 0,
        "system_prompt": 0,
        "file_reads": 0,
        "command_output": 0,
        "others": 0
    }
    
    source = step.get("source", "UNKNOWN")
    step_type = step.get("type", "UNKNOWN")
    
    content = step.get("content") or ""
    thinking = step.get("thinking") or ""
    tool_calls = step.get("tool_calls") or []
    
    content_tokens = estimate_tokens(content)
    thinking_tokens = estimate_tokens(thinking)
    
    # 1. Tool Call Parameters
    tool_calls_tokens = 0
    if tool_calls:
        try:
            tool_calls_tokens = estimate_tokens(json.dumps(tool_calls))
        except Exception:
            pass

    # 2. Categorize based on source and type
    if source in ("USER", "USER_EXPLICIT"):
        cats["user_input"] = content_tokens
    elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
        cats["assistant_output"] = content_tokens + thinking_tokens
        cats["tool_calls"] = tool_calls_tokens
    elif source == "SYSTEM":
        cats["system_prompt"] = content_tokens
    elif source == "TOOL" or step_type not in ("USER_INPUT", "PLANNER_RESPONSE"):
        if step_type == "RUN_COMMAND":
            cats["command_output"] = content_tokens
        elif step_type in ("VIEW_FILE", "READ_FILE"):
            cats["file_reads"] = content_tokens
        elif step_type in ("SEARCH_WEB", "READ_URL_CONTENT", "READ_BROWSER_PAGE"):
            cats["tool_returns"] = content_tokens
        else:
            cats["tool_returns"] = content_tokens
    else:
        cats["others"] = content_tokens + thinking_tokens + tool_calls_tokens
        
    return cats

import sqlite3

MODEL_ENUM_MAP = {
    "MODEL_PLACEHOLDER_M132": "gemini-3-flash-a",
    "MODEL_PLACEHOLDER_M35": "claude-sonnet-4-6",
    "MODEL_PLACEHOLDER_M26": "claude-opus-4-6-thinking"
}

def parse_varint(data, pos):
    val = 0
    shift = 0
    while True:
        b = data[pos]
        val |= (b & 0x7F) << shift
        shift += 7
        pos += 1
        if not (b & 0x80):
            break
    return val, pos

def decode_gen_metadata_protobuf(data):
    """
    Decodes binary gen_metadata protobuf BLOB.
    Returns: (step_idx, model_enum, model_literal, user_setting, input_tokens, output_tokens, timestamp)
    """
    i = 0
    step_idx = None
    model_enum = None
    input_tokens = 0
    output_tokens = 0
    model_literal = None
    user_setting = None
    timestamp = None
    
    try:
        while i < len(data):
            key, i = parse_varint(data, i)
            tag = key >> 3
            wire_type = key & 0x7
            
            if wire_type == 0:
                val, i = parse_varint(data, i)
            elif wire_type == 1:
                i += 8
            elif wire_type == 2:
                length, i = parse_varint(data, i)
                sub_data = data[i:i+length]
                i += length
                
                if tag == 1:
                    j = 0
                    while j < len(sub_data):
                        sub_key, j = parse_varint(sub_data, j)
                        sub_tag = sub_key >> 3
                        sub_wire = sub_key & 0x7
                        if sub_wire == 0:
                            _, j = parse_varint(sub_data, j)
                        elif sub_wire == 1:
                            j += 8
                        elif sub_wire == 2:
                            sub_len, j = parse_varint(sub_data, j)
                            inner_data = sub_data[j:j+sub_len]
                            j += sub_len
                            
                            if sub_tag == 19:
                                model_literal = inner_data.decode("utf-8", errors="ignore")
                            elif sub_tag == 21:
                                user_setting = inner_data.decode("utf-8", errors="ignore")
                            elif sub_tag == 20:
                                try:
                                    prop_key, p_pos = parse_varint(inner_data, 0)
                                    if (prop_key >> 3) == 1 and (prop_key & 0x7) == 2:
                                        k_len, p_pos = parse_varint(inner_data, p_pos)
                                        prop_k = inner_data[p_pos:p_pos+k_len].decode()
                                        p_pos += k_len
                                        prop_val, p_pos = parse_varint(inner_data, p_pos)
                                        if (prop_val >> 3) == 2 and (prop_val & 0x7) == 2:
                                            v_len, p_pos = parse_varint(inner_data, p_pos)
                                            prop_v = inner_data[p_pos:p_pos+v_len].decode()
                                            
                                            if prop_k == "last_step_index":
                                                step_idx = int(prop_v)
                                            elif prop_k == "model_enum":
                                                model_enum = prop_v
                                except Exception:
                                    pass
                            elif sub_tag == 4:
                                k = 0
                                while k < len(inner_data):
                                    m_key, k = parse_varint(inner_data, k)
                                    m_tag = m_key >> 3
                                    m_wire = m_key & 0x7
                                    if m_wire == 0:
                                        m_val, k = parse_varint(inner_data, k)
                                        if m_tag == 2:
                                            input_tokens = m_val
                                        elif m_tag == 3:
                                            output_tokens = m_val
                                    elif m_wire == 1:
                                        k += 8
                                    elif m_wire == 2:
                                        m_len, k = parse_varint(inner_data, k)
                                        k += m_len
                                    else:
                                        k += 1
                            elif sub_tag == 9:
                                try:
                                    t_key, t_pos = parse_varint(inner_data, 0)
                                    if (t_key >> 3) == 4 and (t_key & 0x7) == 2:
                                        t_len, t_pos = parse_varint(inner_data, t_pos)
                                        t_sub = inner_data[t_pos:t_pos+t_len]
                                        t_sub_key, t_sub_pos = parse_varint(t_sub, 0)
                                        if (t_sub_key >> 3) == 1 and (t_sub_key & 0x7) == 0:
                                            ts_val, _ = parse_varint(t_sub, t_sub_pos)
                                            timestamp = ts_val
                                except Exception:
                                    pass
            elif wire_type == 5:
                i += 4
            else:
                break
    except Exception:
        pass
        
    return step_idx, model_enum, model_literal, user_setting, input_tokens, output_tokens, timestamp

def parse_sqlite_convo(db_path, cid):
    """
    Parses conversation's SQLite database to extract all model calls.
    """
    if not os.path.exists(db_path):
        return []
        
    calls = []
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gen_metadata';")
        if not cursor.fetchone():
            return []
            
        cursor.execute("SELECT idx, data FROM gen_metadata;")
        rows = cursor.fetchall()
        
        file_mtime = int(os.path.getmtime(db_path))
        
        for idx, data in rows:
            step_idx, model_enum, model_literal, user_setting, input_tokens, output_tokens, timestamp = decode_gen_metadata_protobuf(data)
            
            if not model_literal and not model_enum:
                continue
            if input_tokens is None and output_tokens is None:
                continue
            if (input_tokens or 0) == 0 and (output_tokens or 0) == 0:
                continue
            
            raw_model_id = model_literal or MODEL_ENUM_MAP.get(model_enum, "unknown_legacy")
            normalized_model_id = normalize_antigravity_model(raw_model_id)
                
            display_model_name = user_setting or ""
            if not display_model_name:
                if normalized_model_id in ("gemini-3-flash-a", "gemini-3.5-flash"):
                    display_model_name = "Gemini 3.5 Flash"
                elif normalized_model_id == "gemini-3.1-pro":
                    display_model_name = "Gemini 3.1 Pro"
                elif normalized_model_id == "claude-sonnet-4-6":
                    display_model_name = "Claude Sonnet 4.6"
                elif normalized_model_id == "claude-opus-4-6-thinking":
                    display_model_name = "Claude Opus 4.6"
                elif normalized_model_id == "gpt-oss-120b":
                    display_model_name = "GPT-OSS 120B"
                else:
                    display_model_name = "未映射模型"
                    
            final_step_idx = step_idx if step_idx is not None else idx
            final_ts = timestamp if timestamp is not None else file_mtime
            call_id = f"{cid}_{final_step_idx}_{raw_model_id}_{input_tokens or 0}_{output_tokens or 0}_{final_ts}_{idx}"
            
            calls.append({
                "call_id": call_id,
                "conversation_id": cid,
                "step_index": final_step_idx,
                "timestamp": final_ts,
                "raw_model_id": raw_model_id,
                "normalized_model_id": normalized_model_id,
                "display_model_name": display_model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            })
    except Exception as e:
        print(f"Error reading SQLite {db_path}: {e}")
    finally:
        if conn:
            conn.close()
            
    return calls

def parse_transcript_file(file_path: str, system_prompt_tokens: int, pricing_scheme: dict):
    """
    Parses a transcript.jsonl file, tracking how input context accumulates turn-by-turn.
    Performs step deduplication by step_id, message_id, step_index or content hash.
    Categorizes tokens and calculates cost based on pricing scheme.
    """
    raw_steps = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                    raw_steps.append(step)
                except Exception:
                    pass
    except Exception:
        return None

    if not raw_steps:
        return None

    # Step deduplication based on key: message_id, step_id, step_index, or content hash
    seen_keys = set()
    deduped_steps = []
    
    for step in raw_steps:
        dup_key = None
        if "step_id" in step and step["step_id"] is not None:
            dup_key = f"step_id:{step['step_id']}"
        elif "message_id" in step and step["message_id"] is not None:
            dup_key = f"message_id:{step['message_id']}"
        elif "step_index" in step and step["step_index"] is not None:
            dup_key = f"step_index:{step['step_index']}"
            
        if not dup_key:
            # Fallback to MD5 of step content
            content_str = step.get("content") or ""
            thinking_str = step.get("thinking") or ""
            combined = content_str + thinking_str
            content_hash = hashlib.md5(combined.encode("utf-8")).hexdigest()
            dup_key = f"hash:{content_hash}"
            
        if dup_key in seen_keys:
            continue
        seen_keys.add(dup_key)
        deduped_steps.append(step)
        
    # Sort steps by step_index
    deduped_steps.sort(key=lambda s: s.get("step_index", 0))

    # Calculate token counts for each individual step
    step_token_sums = []
    step_cats = []
    
    for step in deduped_steps:
        cats = classify_tokens(step)
        step_cats.append(cats)
        # Sum of original tokens in this step
        step_token_sums.append(sum(cats.values()))

    # Calculate context accumulations
    parsed_steps = []
    accumulated_context_tokens = 0
    total_assistant_output_tokens = 0
    total_original_tokens = sum(step_token_sums)
    
    # Categories aggregate for original content
    original_cats = {
        "user_input": 0,
        "assistant_output": 0,
        "tool_calls": 0,
        "tool_returns": 0,
        "system_prompt": 0,
        "file_reads": 0,
        "command_output": 0,
        "others": 0
    }
    for sc in step_cats:
        for k, v in sc.items():
            original_cats[k] += v

    # Model call boundaries calculation
    model_calls_count = 0
    in_rate = pricing_scheme["input_per_million"]
    out_rate = pricing_scheme["output_per_million"]

    for idx, step in enumerate(deduped_steps):
        step_orig_tokens = step_token_sums[idx]
        input_context_tokens = 0
        output_tokens = 0
        
        # Identify model calls
        is_model_call = step.get("source") == "MODEL" and step.get("type") == "PLANNER_RESPONSE"
        
        if is_model_call:
            # Context sent = system prompt + sum of tokens of all previous steps
            input_context_tokens = system_prompt_tokens + sum(step_token_sums[:idx])
            output_tokens = step_orig_tokens
            
            accumulated_context_tokens += input_context_tokens
            total_assistant_output_tokens += output_tokens
            model_calls_count += 1
            
        parsed_steps.append({
            "step_index": step.get("step_index", idx),
            "source": step.get("source", "UNKNOWN"),
            "type": step.get("type", "UNKNOWN"),
            "status": step.get("status", "UNKNOWN"),
            "created_at": step.get("created_at", ""),
            "tokens": step_orig_tokens,
            "input_context_tokens": input_context_tokens,
            "output_tokens": output_tokens,
            "categories": step_cats[idx],
            "content_preview": step.get("content", "")[:200] + "..." if step.get("content") else ""
        })

    # Estimate conversation title
    title = "无标题对话"
    for step in deduped_steps:
        if step.get("source") in ("USER", "USER_EXPLICIT") and step.get("content"):
            cleaned = re.sub(r"<USER_REQUEST>|</USER_REQUEST>", "", step["content"]).strip()
            cleaned = cleaned.split("\n")[0]
            if len(cleaned) > 50:
                title = cleaned[:50] + "..."
            else:
                title = cleaned
            break
            
    # Conversation timestamps
    created_at = deduped_steps[0].get("created_at", "")
    last_active = deduped_steps[-1].get("created_at", "")
    
    # Cost calculations
    # 83.20M Token corresponding to $6.3197 logic: (tokens / 1,000,000) * rate_per_million
    cost = (accumulated_context_tokens / 1_000_000) * in_rate + (total_assistant_output_tokens / 1_000_000) * out_rate

    local_date = to_local_date(last_active)
            
    return {
        "title": title,
        "created_at": created_at,
        "last_active": last_active,
        "steps_count": len(deduped_steps),
        "model_calls_count": model_calls_count,
        "original_tokens": total_original_tokens,
        "accumulated_context_tokens": accumulated_context_tokens,
        "assistant_output_tokens": total_assistant_output_tokens,
        "original_categories": original_cats,
        "cost": cost,
        "local_date": local_date,
        "steps": parsed_steps
    }

def get_codex_auth_info():
    """Return non-sensitive login status only; never inspect credential files."""
    result = {"auth_mode": "Unknown", "plan_type": "unknown_plan"}
    try:
        proc = subprocess.run(["codex", "login", "status"], capture_output=True,
                              text=True, timeout=10, check=False)
        text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
        if "api key" in text or "api" in text and "logged" in text:
            result["auth_mode"] = "API"
        elif "chatgpt" in text or "logged in" in text or proc.returncode == 0:
            result["auth_mode"] = "ChatGPT"
    except (OSError, subprocess.TimeoutExpired):
        pass
    return result

def scan_codex_conversations(settings, cache):
    import glob
    auth_info = get_codex_auth_info()
    files = sorted(set(glob.glob(os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True) +
                       glob.glob(os.path.expanduser("~/.codex/archived_sessions/**/*.jsonl"), recursive=True)))
    codex_cache = cache.setdefault("codex_files", {})
    seen_ids = set(cache.setdefault("processed_event_ids", []))
    all_calls, stats = [], {"sessions_scanned": 0, "raw_token_count_events": 0,
        "missing_usage": 0, "duplicate_snapshots": 0, "unchanged_totals": 0,
        "resets": 0, "delta_matches": 0, "delta_mismatches": 0,
        "valid_calls": 0, "unverified_calls": 0, "active_files": 0, "archived_files": 0,
        "duplicate_active_archived": 0}
    plan_types = []

    def num(u, key):
        value = u.get(key)
        return value if isinstance(value, int) and value >= 0 else None

    def usage_tuple(u):
        return tuple(num(u, k) for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens"))

    for path in files:
        if not os.path.isfile(path): continue
        stats["sessions_scanned"] += 1
        if "/archived_sessions/" in path: stats["archived_files"] += 1
        else: stats["active_files"] += 1
        size, mtime = os.path.getsize(path), int(os.path.getmtime(path))
        old = codex_cache.get(path, {})
        session_id = old.get("session_id")
        if not session_id:
            session_id = os.path.basename(path).removeprefix("rollout-").removesuffix(".jsonl")
            try:
                with open(path, "r", encoding="utf-8") as meta_file:
                    for meta_line in meta_file:
                        meta = json.loads(meta_line)
                        if meta.get("type") == "session_meta":
                            meta_payload = meta.get("payload") or {}
                            session_id = str(meta_payload.get("session_id") or meta_payload.get("id") or session_id)
                            break
            except (OSError, ValueError, UnicodeError):
                pass
        incremental = size >= old.get("size", 0) and old.get("offset", 0) > 0
        start = old.get("offset", 0) if incremental else 0
        state = old if incremental else {}
        prev = state.get("last_total")
        segment = int(state.get("segment", 0))
        model = state.get("model")
        turn_id = state.get("turn_id")
        line_no = int(state.get("line_number", 0)) if incremental else 0
        event_id = None
        try:
            with open(path, "r", encoding="utf-8") as f:
                if start: f.seek(start)
                for raw_line in f:
                    line_no += 1
                    if not raw_line.strip(): continue
                    try: event = json.loads(raw_line)
                    except Exception: continue
                    payload = event.get("payload") or {}
                    if event.get("type") == "turn_context":
                        model = payload.get("model") or model
                        turn_id = payload.get("turn_id") or turn_id
                    elif event.get("type") == "event_msg":
                        et = payload.get("type")
                        if et == "task_started": turn_id = payload.get("turn_id") or turn_id
                        if et == "thread_settings": model = (payload.get("thread_settings") or {}).get("model") or model
                        if et != "token_count": continue
                        stats["raw_token_count_events"] += 1
                        info = payload.get("info") or {}
                        total, last = info.get("total_token_usage"), info.get("last_token_usage")
                        limits = info.get("rate_limits") or payload.get("rate_limits") or {}
                        if limits.get("plan_type"): plan_types.append(str(limits["plan_type"]))
                        if not isinstance(total, dict) or not isinstance(last, dict):
                            stats["missing_usage"] += 1; continue
                        tv, lv = usage_tuple(total), usage_tuple(last)
                        if any(v is None for v in tv + lv):
                            stats["missing_usage"] += 1; continue
                        event_id = hashlib.sha256(f"{session_id}|{segment}|{event.get('timestamp')}|{model or 'missing_model'}|{tv[0]}|{tv[1]}|{tv[2]}|{tv[3]}".encode()).hexdigest()
                        if event_id in seen_ids:
                            stats["duplicate_snapshots"] += 1; continue
                        seen_ids.add(event_id)
                        if prev is None:
                            if tv == lv:
                                valid, delta = True, tv
                                stats["delta_matches"] += 1
                            else:
                                valid, delta = False, lv
                                stats["delta_mismatches"] += 1
                        elif any(tv[i] < prev[i] for i in range(5)):
                            segment += 1; stats["resets"] += 1
                            valid, delta = (tv == lv), lv
                            stats["delta_matches" if valid else "delta_mismatches"] += 1
                        elif tv == prev:
                            stats["unchanged_totals"] += 1; prev = tv; continue
                        else:
                            delta = tuple(tv[i] - prev[i] for i in range(5))
                            valid = delta == lv
                            stats["delta_matches" if valid else "delta_mismatches"] += 1
                        prev = tv
                        raw_model = model or "missing_model"
                        normalized = raw_model
                        display = {"gpt-5.6-luna": "GPT-5.6 Luna", "codex-auto-review": "Codex Auto Review", "missing_model": "模型未知"}.get(raw_model, raw_model)
                        if valid:
                            stats["valid_calls"] += 1
                            all_calls.append({"call_id": event_id, "session_id": session_id, "turn_id": turn_id,
                                "timestamp": event.get("timestamp") or "", "local_date": to_local_date(event.get("timestamp") or ""), "raw_model_id": raw_model,
                                "normalized_model_id": normalized, "display_name": display,
                                "input_tokens": lv[0], "cached_input_tokens": lv[1], "output_tokens": lv[2],
                            "reasoning_output_tokens": lv[3], "pricing_status": "unpriced" if raw_model != "missing_model" else "unknown_model"})
                        elif not valid:
                            stats["unverified_calls"] += 1
                offset = f.tell()
        except (OSError, UnicodeError):
            continue
        codex_cache[path] = {"file_id": hashlib.sha256(path.encode()).hexdigest(), "offset": offset,
            "size": size, "mtime": mtime, "last_event_id": event_id if 'event_id' in locals() else None,
            "last_total": prev, "segment": segment, "model": model, "turn_id": turn_id,
            "session_id": session_id,
            "line_number": line_no}
    cache["processed_event_ids"] = sorted(seen_ids)
    auth_info["plan_type"] = plan_types[-1] if plan_types else "unknown_plan"
    if str(auth_info["plan_type"]).lower() == "plus":
        auth_info["plan_type"] = "Plus"
    stats["duplicate_active_archived"] = max(0, stats["duplicate_snapshots"])
    return all_calls, auth_info, stats


# ─────────────────────────────────────────────────────────────────────────────
# Quota event scanner — reads RESOURCE_EXHAUSTED errors from transcripts
# to surface the last known quota reset windows per model group.
# Only reads local transcript.jsonl files; no network calls.
# ─────────────────────────────────────────────────────────────────────────────

def _parse_resets_in_seconds(resets_in: str) -> int:
    """Parse 'Xh Ym Zs' or '119h49m32s' into total seconds."""
    total = 0
    h_match = re.search(r'(\d+)h', resets_in)
    m_match = re.search(r'(\d+)m', resets_in)
    s_match = re.search(r'(\d+)s', resets_in)
    if h_match: total += int(h_match.group(1)) * 3600
    if m_match: total += int(m_match.group(1)) * 60
    if s_match: total += int(s_match.group(1))
    return total


def _infer_model_group(model_id: str) -> str:
    """Infer model group from model id string."""
    if not model_id:
        return "unknown"
    ml = model_id.lower()
    if "gemini" in ml:
        return "gemini"
    if "claude" in ml:
        return "claude"
    if "gpt" in ml or "codex" in ml or "openai" in ml:
        return "gpt"
    return "unknown"


def scan_quota_events() -> list:
    """
    Scan all brain transcript.jsonl files for RESOURCE_EXHAUSTED quota errors.
    Returns a list of quota events, deduplicated and sorted by event_time desc.
    Each event: {event_time, reset_time, model_group, resets_in_seconds, source_db}
    """
    settings = load_settings()
    app_data_dirs = settings.get("app_data_dirs", DEFAULT_SETTINGS["app_data_dirs"])

    seen_keys = set()
    events = []

    quota_pattern = re.compile(
        r'RESOURCE_EXHAUSTED.*?Individual quota reached.*?Resets in ([\dhms]+)',
        re.DOTALL
    )
    model_id_pattern = re.compile(r'"model_id"\s*:\s*"([^"]+)"')

    for base_dir in app_data_dirs:
        brain_dir = os.path.join(base_dir, "brain")
        if not os.path.isdir(brain_dir):
            continue

        try:
            cids = os.listdir(brain_dir)
        except (PermissionError, OSError):
            continue

        for cid in cids:
            transcript_path = os.path.join(
                brain_dir, cid, ".system_generated", "logs", "transcript.jsonl"
            )
            if not os.path.isfile(transcript_path):
                continue

            try:
                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                        except (json.JSONDecodeError, ValueError):
                            continue

                        content = str(entry.get("content", ""))
                        if "RESOURCE_EXHAUSTED" not in content:
                            continue

                        m = quota_pattern.search(content)
                        if not m:
                            continue

                        resets_in_str = m.group(1)
                        resets_in_sec = _parse_resets_in_seconds(resets_in_str)

                        # Timestamp from the transcript entry
                        raw_ts = entry.get("timestamp") or entry.get("created_at") or ""
                        event_dt = None
                        if raw_ts:
                            for fmt in [
                                "%Y-%m-%dT%H:%M:%SZ",
                                "%Y-%m-%dT%H:%M:%S%z",
                                "%Y-%m-%dT%H:%M:%S.%fZ",
                            ]:
                                try:
                                    event_dt = datetime.strptime(raw_ts[:25], fmt[:len(raw_ts[:25])])
                                    break
                                except ValueError:
                                    pass
                        if event_dt is None:
                            continue

                        # ISO strings (UTC)
                        event_time_iso = event_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                        from datetime import timedelta
                        reset_dt = event_dt + timedelta(seconds=resets_in_sec)
                        reset_time_iso = reset_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

                        # Infer model group from surrounding content
                        model_id_match = model_id_pattern.search(content)
                        model_id = model_id_match.group(1) if model_id_match else ""
                        model_group = _infer_model_group(model_id)

                        # Deduplicate on (event_time, model_group, resets_in_str)
                        dedup_key = f"{event_time_iso}|{model_group}|{resets_in_str}"
                        if dedup_key in seen_keys:
                            continue
                        seen_keys.add(dedup_key)

                        events.append({
                            "event_time": event_time_iso,
                            "reset_time": reset_time_iso,
                            "resets_in_seconds": resets_in_sec,
                            "resets_in_text": resets_in_str,
                            "model_group": model_group,
                            "model_id": model_id,
                            "source": "antigravity",
                        })

            except (OSError, UnicodeError):
                continue

    # Sort by event_time descending, keep at most 20 most recent events
    events.sort(key=lambda e: e["event_time"], reverse=True)
    return events[:20]


CODEX_DEFAULT_PRICES = {}

def scan_conversations():
    """
    Scans all brain directories in Antigravity/CLI configurations,
    and runs the Codex token scans.
    Uses modified-time, size, and content MD5 hash caching to parse efficiently.
    Returns: conversations, codex_calls, codex_auth_info, scanner_stats
    """
    settings = load_settings()
    system_prompt_tokens = settings.get("system_prompt_tokens", 0)
    model_prices = settings.get("model_prices", DEFAULT_SETTINGS["model_prices"])
    
    # Fallback legacy pricing if not defined or DB deleted
    legacy_in_rate = model_prices.get("gemini-3-flash-a", {}).get("input_price_per_million", 0.075)
    legacy_out_rate = model_prices.get("gemini-3-flash-a", {}).get("output_price_per_million", 0.30)

    start_time = time.time()
    files_scanned = 0
    files_skipped = 0
    files_error = 0

    # Load cache
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass

    conversations = {}
    
    for base_dir in settings.get("app_data_dirs", []):
        brain_dir = os.path.join(base_dir, "brain")
        if not os.path.exists(brain_dir):
            continue
            
        try:
            convo_ids = os.listdir(brain_dir)
        except Exception:
            continue
            
        for cid in convo_ids:
            convo_path = os.path.join(brain_dir, cid)
            if not os.path.isdir(convo_path):
                continue
                
            # Locate transcript file (prioritize transcript.jsonl, fallback transcript_full.jsonl)
            transcript_path = os.path.join(convo_path, ".system_generated", "logs", "transcript.jsonl")
            if not os.path.exists(transcript_path):
                transcript_path = os.path.join(convo_path, ".system_generated", "logs", "transcript_full.jsonl")
                if not os.path.exists(transcript_path):
                    continue
                    
            try:
                stat = os.stat(transcript_path)
                mtime = stat.st_mtime
                size = stat.st_size
            except Exception:
                files_error += 1
                continue

            cache_key = f"{cid}_{transcript_path}"
            
            # Check cache validity using mtime, size, and hash
            file_hash = ""
            cache_hit = False
            if cache_key in cache:
                cached_item = cache[cache_key]
                if cached_item.get("mtime") == mtime and cached_item.get("size") == size:
                    cached_hash = cached_item.get("hash")
                    if cached_hash:
                        file_hash = cached_hash
                        cache_hit = True
                    else:
                        file_hash = get_file_hash(transcript_path)
                        if file_hash == cached_item.get("hash"):
                            cache_hit = True

            if cache_hit:
                conversations[cid] = cache[cache_key]["data"]
                # Re-calculate cost using current model prices
                cost = 0.0
                for c in conversations[cid].get("model_calls", []):
                    c["normalized_model_id"] = normalize_antigravity_model(
                        c.get("raw_model_id") or c.get("normalized_model_id")
                    )
                    mid = c["normalized_model_id"]
                    c["cost"] = float(cost_for_call(mid, c["input_tokens"], 0, c["output_tokens"], model_prices))
                    cost += c["cost"]
                conversations[cid]["cost"] = cost
                files_skipped += 1
                continue

            # Cache miss -> parse convo
            if not file_hash:
                file_hash = get_file_hash(transcript_path)
                
            # Parse baseline details from transcript JSONL
            dummy_pricing = {"input_per_million": 0.0, "output_per_million": 0.0}
            data = parse_transcript_file(transcript_path, system_prompt_tokens, dummy_pricing)
            if data:
                base_dir = os.path.dirname(brain_dir)
                db_path = os.path.join(base_dir, "conversations", f"{cid}.db")
                
                calls = parse_sqlite_convo(db_path, cid)
                
                if calls:
                    data["model_calls"] = calls
                    data["accumulated_context_tokens"] = sum(c["input_tokens"] for c in calls)
                    data["assistant_output_tokens"] = sum(c["output_tokens"] for c in calls)
                    data["original_tokens"] = data["accumulated_context_tokens"] + data["assistant_output_tokens"]
                    data["model_calls_count"] = len(calls)
                    
                    cost = 0.0
                    for c in calls:
                        mid = c["normalized_model_id"]
                        c["cost"] = float(cost_for_call(mid, c["input_tokens"], 0, c["output_tokens"], model_prices))
                        cost += c["cost"]
                    data["cost"] = cost
                else:
                    cost = (data["accumulated_context_tokens"] / 1_000_000) * legacy_in_rate + (data["assistant_output_tokens"] / 1_000_000) * legacy_out_rate
                    data["cost"] = cost
                    data["model_calls_count"] = 0
                    data["model_calls"] = [
                        {
                            "call_id": f"{cid}_legacy_fallback",
                            "conversation_id": cid,
                            "step_index": 0,
                            "timestamp": int(stat.st_mtime),
                            "raw_model_id": "unknown_legacy",
                            "normalized_model_id": "unknown_legacy",
                            "display_model_name": "未知历史模型",
                            "input_tokens": data["accumulated_context_tokens"],
                            "output_tokens": data["assistant_output_tokens"],
                            "cost": cost
                        }
                    ]
                
                data["id"] = cid
                data["path"] = transcript_path
                conversations[cid] = data
                files_scanned += 1
                
                cache[cache_key] = {
                    "mtime": mtime,
                    "size": size,
                    "hash": file_hash,
                    "data": data
                }
            else:
                files_error += 1

    # Codex scan integration
    codex_calls, codex_auth_info, codex_stats = scan_codex_conversations(settings, cache)

    # Dynamic registration of newly discovered models
    all_discovered_models = set()
    for cid, convo in conversations.items():
        for call in convo.get("model_calls", []):
            all_discovered_models.add(call["normalized_model_id"])
            
    settings_updated = False
    # Force standard tier for calculation, but keep settings value as is for compatibility
    tier = "standard"
    gem = model_prices.get("gemini-3-flash-a")
    if isinstance(gem, dict) and not gem.get("user_overridden", False):
        tier_prices = {
            "standard": {"input_price_per_million": 1.50, "cached_input_price_per_million": 0.15, "output_price_per_million": 9.00},
            "priority": {"input_price_per_million": 2.70, "cached_input_price_per_million": 0.27, "output_price_per_million": 16.20},
        }[tier]
        if any(gem.get(k) != v for k, v in tier_prices.items()):
            gem.update(tier_prices)
            settings_updated = True
    for mid in all_discovered_models:
        if mid not in model_prices:
            model_prices[mid] = {
                "display_name": mid,
                "provider": "Unknown",
                "input_price_per_million": 0.0,
                "output_price_per_million": 0.0,
                "pricing_profile": "api_standard_equivalent",
                "pricing_source": "unmapped",
                "pricing_verified_at": datetime.now().strftime("%Y-%m-%d"),
                "user_overridden": False,
                "actual_billing_confirmed": False
            }
            settings_updated = True
            
    for call in codex_calls:
        mid = call["normalized_model_id"]
        if mid in DEFAULT_SETTINGS["model_prices"] and not model_prices.get(mid, {}).get("user_overridden", False):
            model_prices[mid] = dict(DEFAULT_SETTINGS["model_prices"][mid])
        elif mid == "codex-auto-review" and not model_prices.get(mid, {}).get("user_overridden", False):
            model_prices[mid] = {
                "display_name": "Codex Auto Review", "provider": "OpenAI",
                "input_price_per_million": 0.0, "cached_input_price_per_million": 0.0,
                "output_price_per_million": 0.0, "pricing_unit": "credits",
                "pricing_profile": "unpriced", "pricing_source": "unpriced",
                "pricing_verified_at": datetime.now().strftime("%Y-%m-%d"),
                "user_overridden": False, "actual_extra_charge_confirmed": False,
                "raw_model_id": "codex-auto-review"
            }
        if mid not in model_prices:
            if mid in CODEX_DEFAULT_PRICES:
                model_prices[mid] = dict(CODEX_DEFAULT_PRICES[mid])
            else:
                model_prices[mid] = {
                    "display_name": mid,
                    "provider": "OpenAI",
                    "input_price_per_million": 0.0,
                    "cached_input_price_per_million": 0.0,
                    "output_price_per_million": 0.0,
                    "pricing_unit": "credits",
                "pricing_profile": "unmapped",
                    "pricing_source": "unmapped",
                    "pricing_verified_at": "2026-07-17",
                    "user_overridden": False,
                    "actual_extra_charge_confirmed": False,
                    "raw_model_id": call["raw_model_id"]
                }
            settings_updated = True
            
    if settings_updated:
        settings["model_prices"] = model_prices
        save_settings(settings)

    # Save updated cache
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    scan_duration_ms = int((time.time() - start_time) * 1000)
    last_scan_time = datetime.now().astimezone().isoformat(timespec="seconds")

    scanner_stats = {
        "last_scan_time": last_scan_time,
        "scan_duration_ms": scan_duration_ms,
        "files_scanned": files_scanned + len(set(c["session_id"] for c in codex_calls)),
        "files_skipped": files_skipped,
        "files_error": files_error,
        "codex": codex_stats
    }
    global LAST_SCAN_METADATA
    LAST_SCAN_METADATA = {"codex_calls": codex_calls, "codex_auth_info": codex_auth_info,
                          "scanner_stats": scanner_stats}
    return conversations, scanner_stats


def get_quota_status(convos, codex_calls):
    """
    Get estimated remaining percentage and reset times for quotas based on usage
    and hard error logs (429 RESOURCE_EXHAUSTED).
    """
    return {}


def get_latest_codex_rate_limits() -> tuple:
    """Scan Codex session files recursively, find all rate_limits events,
    and return the tuple (latest_rate_limits_dict, event_timestamp_str).
    """
    import glob
    home = os.path.expanduser("~")
    files = []
    for folder in [".codex/sessions", ".codex/archived_sessions"]:
        d = os.path.join(home, folder)
        if os.path.isdir(d):
            try:
                # Recursive glob to capture YYYY/MM/DD and nested files
                files.extend(glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True))
            except:
                pass
                
    events = []
    for p in files:
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "rate_limits" not in line:
                        continue
                    try:
                        ev = json.loads(line)
                        payload = ev.get("payload") or {}
                        info = payload.get("info") or {}
                        limits = info.get("rate_limits") or payload.get("rate_limits") or {}
                        if limits and (limits.get("primary") or limits.get("secondary")):
                            ts = ev.get("timestamp")
                            if ts:
                                events.append((ts, limits))
                    except:
                        continue
        except:
            continue
            
    if not events:
        return {}, ""
        
    # Sort events by timestamp string globally
    events.sort(key=lambda x: x[0])
    return events[-1][1], events[-1][0]


def find_antigravity_cdp_port() -> int:
    import subprocess, re
    try:
        out = subprocess.check_output(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if "Antigravi" in line or "Antigravity" in line:
                m = re.search(r":(\d+)\s+\(LISTEN\)", line)
                if m:
                    return int(m.group(1))
    except:
        pass
    return None


ANTIGRAVITY_QUOTA_ORDER = [
    ("gemini", "weekly"),
    ("gemini", "five_hour"),
    ("claude_gpt", "weekly"),
    ("claude_gpt", "five_hour"),
]

ANTIGRAVITY_QUOTA_NAMES = {
    ("gemini", "weekly"): "Gemini 周额度",
    ("gemini", "five_hour"): "Gemini 五小时额度",
    ("claude_gpt", "weekly"): "Claude/GPT 周额度",
    ("claude_gpt", "five_hour"): "Claude/GPT 五小时额度",
}

ANTIGRAVITY_QUOTA_RPC_PATH = "/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"
ANTIGRAVITY_QUOTA_SOURCE_PATH = "language_server_rpc:/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"


def discover_antigravity_rpc_origin(cdp_port=None) -> str:
    """Find the current language_server HTTPS origin without assuming a fixed port."""
    import urllib.request

    port = cdp_port or find_antigravity_cdp_port()
    if not port:
        return ""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=1.5) as response:
            targets = json.loads(response.read().decode("utf-8"))
    except Exception:
        return ""
    for target in targets if isinstance(targets, list) else []:
        if target.get("type") != "page":
            continue
        match = re.match(r"^(https://127\.0\.0\.1:\d+)(?:/|$)", target.get("url", ""))
        if match:
            return match.group(1)
    return ""


def find_antigravity_language_server_csrf_token() -> str:
    """Read the ephemeral local-RPC CSRF value from the running server process.

    The value is used only for the loopback request and is never logged or persisted.
    It is not a Google account credential, cookie, OAuth token, or Authorization header.
    """
    import shlex

    try:
        output = subprocess.check_output(
            ["ps", "-ax", "-ww", "-o", "command="],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
    except Exception:
        return ""
    marker = "/Antigravity.app/Contents/Resources/bin/language_server"
    for line in output.splitlines():
        if marker not in line or "--standalone" not in line:
            continue
        try:
            args = shlex.split(line)
            index = args.index("--csrf_token")
            token = args[index + 1]
        except (ValueError, IndexError):
            continue
        if token and not token.startswith("-"):
            return token
    return ""


def encode_grpc_web_json_message(payload: dict) -> bytes:
    import struct

    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return b"\x00" + struct.pack(">I", len(encoded)) + encoded


def decode_grpc_web_json_message(payload: bytes) -> dict:
    """Decode the first data frame, ignoring any following gRPC-Web trailer frame."""
    import struct

    offset = 0
    while offset + 5 <= len(payload):
        flags = payload[offset]
        size = struct.unpack(">I", payload[offset + 1:offset + 5])[0]
        start = offset + 5
        end = start + size
        if end > len(payload):
            raise ValueError("truncated gRPC-Web frame")
        if flags & 0x80 == 0:
            decoded = json.loads(payload[start:end].decode("utf-8"))
            if not isinstance(decoded, dict):
                raise ValueError("unexpected gRPC-Web JSON payload")
            return decoded
        offset = end
    raise ValueError("gRPC-Web response contained no data frame")


def normalize_antigravity_quota_rpc_response(payload: dict, observed_at: str) -> dict:
    """Validate and normalize the four official quota buckets returned by the RPC."""
    response = payload.get("response") if isinstance(payload, dict) else None
    groups = response.get("groups") if isinstance(response, dict) else None
    if not isinstance(groups, list):
        return {"status": "unavailable", "message": "暂时无法读取官方额度", "items": []}

    group_map = {"Gemini Models": "gemini", "Claude and GPT models": "claude_gpt"}
    window_map = {"weekly": "weekly", "5h": "five_hour", "five_hour": "five_hour"}
    deduped = {}
    for group in groups:
        if not isinstance(group, dict):
            continue
        group_id = group_map.get(group.get("displayName"))
        if not group_id:
            continue
        for bucket in group.get("buckets", []):
            if not isinstance(bucket, dict):
                continue
            key = (group_id, window_map.get(bucket.get("window")))
            if key not in ANTIGRAVITY_QUOTA_NAMES or key in deduped:
                continue
            try:
                fraction = float(bucket["remainingFraction"])
            except (KeyError, TypeError, ValueError):
                continue
            reset_time = bucket.get("resetTime")
            if not 0 <= fraction <= 1 or not isinstance(reset_time, str) or not reset_time:
                continue
            raw_percent = round(fraction * 100)
            deduped[key] = {
                "source": "antigravity",
                "name": ANTIGRAVITY_QUOTA_NAMES[key],
                "group": key[0],
                "window": key[1],
                "raw_percent": raw_percent,
                "percent_semantics": "remaining",
                "used_percent": 100 - raw_percent,
                "reset_time": reset_time,
                "observed_at": observed_at,
                "confidence": "official_live",
                "original_field_name": "bucket.remaining.remainingFraction",
                "source_path": ANTIGRAVITY_QUOTA_SOURCE_PATH,
            }

    items = [deduped[key] for key in ANTIGRAVITY_QUOTA_ORDER if key in deduped]
    if len(items) != len(ANTIGRAVITY_QUOTA_ORDER):
        return {"status": "unavailable", "message": "暂时无法读取官方额度", "items": []}
    return {"status": "official_live", "message": "", "items": items}


def read_antigravity_live_quota() -> dict:
    """Refresh current quota through Antigravity's official local language_server RPC."""
    import ssl
    import urllib.request

    origin = discover_antigravity_rpc_origin()
    csrf_token = find_antigravity_language_server_csrf_token()
    if not origin or not csrf_token:
        return {"status": "unavailable", "message": "暂时无法读取官方额度", "items": []}
    try:
        request = urllib.request.Request(
            origin + ANTIGRAVITY_QUOTA_RPC_PATH,
            data=encode_grpc_web_json_message({"forceRefresh": True}),
            method="POST",
            headers={
                "content-type": "application/grpc-web+json",
                "x-grpc-web": "1",
                "x-user-agent": "grpc-web-javascript/0.1",
                "x-codeium-csrf-token": csrf_token,
            },
        )
        with urllib.request.urlopen(
            request,
            context=ssl._create_unverified_context(),
            timeout=8,
        ) as response:
            payload = decode_grpc_web_json_message(response.read())
        observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        return normalize_antigravity_quota_rpc_response(payload, observed_at)
    except Exception:
        return {"status": "unavailable", "message": "暂时无法读取官方额度", "items": []}


def read_codex_accessibility_quota() -> dict:
    """Compatibility entry point; Accessibility is no longer automated or clicked."""
    return {"status": "unavailable", "message": "暂时无法读取当前官方额度", "items": []}


def codex_used_percent(raw_percent, semantics: str):
    """Convert a semantically identified official percentage into used percent."""
    try:
        raw = float(raw_percent)
    except (TypeError, ValueError):
        return None
    if not 0 <= raw <= 100 or semantics not in {"used", "remaining"}:
        return None
    return raw if semantics == "used" else 100.0 - raw


def parse_reset_entitlements(result: dict, observed_at: str) -> dict:
    if not isinstance(result, dict):
        return {
            "status": "unavailable",
            "message": "暂时无法读取可用重置",
            "available_count": None,
            "items": []
        }
    
    reset_credits = result.get("rateLimitResetCredits")
    if not isinstance(reset_credits, dict):
        return {
            "status": "unavailable",
            "message": "暂时无法读取可用重置",
            "available_count": None,
            "items": []
        }
        
    raw_count = reset_credits.get("availableCount")
    try:
        available_count = int(raw_count) if raw_count is not None else None
    except (TypeError, ValueError, OverflowError):
        available_count = None
    
    credits_list = reset_credits.get("credits") or []
    items = []
    
    for item in credits_list:
        if not isinstance(item, dict):
            continue
        expires_at_timestamp = item.get("expiresAt") or item.get("expires_at")
        expires_at_str = None
        expires_on_str = None
        
        if expires_at_timestamp is not None:
            try:
                expires_at_str = datetime.fromtimestamp(int(expires_at_timestamp), timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            except (ValueError, OverflowError, TypeError):
                pass
                
        expires_on_val = item.get("expires_on") or item.get("expiresOn")
        if expires_on_val is not None:
            expires_on_str = str(expires_on_val)
            
        raw_expiration = str(expires_at_timestamp or expires_on_val or "")
        
        status = str(item.get("status") or "unknown")
        items.append({
            "id": str(item.get("id") or ""),
            "type": str(item.get("resetType") or "unknown_reset"),
            "status": status,
            "granted_at": str(item.get("grantedAt") or ""),
            "display_name": str(item.get("title") or "Reset"),
            "expires_on": expires_on_str,
            "expires_at": expires_at_str,
            "raw_expiration": raw_expiration
        })
        
    available_items = [item for item in items if item.get("status", "").lower() == "available"]
    count_semantics = "official" if available_count is not None else "derived_from_available_items"
    if available_count is None:
        available_count = len(available_items)
    if available_count != len(available_items):
        print(
            f"Codex reset entitlement count mismatch: official={available_count} available_items={len(available_items)}",
            file=sys.stderr,
        )
        
    return {
        "status": "official_live",
        "message": None,
        "available_count": available_count,
        "items": items,
        "count_semantics": count_semantics,
        "source_path": "codex_app_server_rpc",
        "original_field_name": "rateLimitResetCredits.credits",
        "available_count_field_name": "rateLimitResetCredits.availableCount",
        "expires_at_field_name": "rateLimitResetCredits.credits[].expiresAt",
        "observed_at": observed_at
    }


def normalize_codex_app_server_rate_limits(result: dict, observed_at: str) -> dict:
    """Normalize the official account/rateLimits/read snapshot into rate limits and reset entitlements."""
    if not isinstance(result, dict):
        return {
            "status": "unavailable",
            "message": "暂时无法读取当前官方额度",
            "items": [],
            "reset_entitlements": {
                "status": "unavailable",
                "message": "暂时无法读取可用重置",
                "available_count": None,
                "items": []
            }
        }

    # 1. Parse rate limits
    rate_limits_dict = {"status": "unavailable", "message": "暂时无法读取当前官方额度", "items": []}
    by_id = result.get("rateLimitsByLimitId")
    snapshot = by_id.get("codex") if isinstance(by_id, dict) else None
    field_prefix = "rateLimitsByLimitId.codex"
    if not isinstance(snapshot, dict):
        candidate = result.get("rateLimits")
        if isinstance(candidate, dict) and candidate.get("limitId") in {None, "codex"}:
            snapshot = candidate
            field_prefix = "rateLimits"
            
    if isinstance(snapshot, dict):
        selected_name = None
        selected_window = None
        for name in ("primary", "secondary"):
            window = snapshot.get(name)
            if isinstance(window, dict) and window.get("windowDurationMins") == 7 * 24 * 60:
                selected_name, selected_window = name, window
                break
        if selected_window is not None:
            raw_percent = selected_window.get("usedPercent")
            used_percent = codex_used_percent(raw_percent, "used")
            resets_at = selected_window.get("resetsAt")
            if used_percent is not None and isinstance(resets_at, int) and resets_at > 0:
                try:
                    reset_time = datetime.fromtimestamp(resets_at, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                    plan_type = snapshot.get("planType")
                    group = "chatgpt_plus" if plan_type == "plus" else f"chatgpt_{plan_type or 'unknown'}"
                    display_plan = "Plus" if plan_type == "plus" else str(plan_type or "Unknown").replace("_", " ").title()
                    rate_limits_dict = {
                        "status": "official_live",
                        "message": "",
                        "items": [{
                            "source": "codex",
                            "name": f"ChatGPT {display_plan} 周额度",
                            "group": group,
                            "window": "weekly",
                            "raw_percent": float(raw_percent),
                            "used_percent": used_percent,
                            "percent_semantics": "used",
                            "reset_time": reset_time,
                            "observed_at": observed_at,
                            "confidence": "official_live",
                            "original_field_name": f"{field_prefix}.{selected_name}.usedPercent",
                            "source_path": "codex_app_server_rpc",
                        }]
                    }
                except Exception:
                    pass

    # 2. Parse reset entitlements
    reset_ent = {
        "status": "unavailable",
        "message": "暂时无法读取可用重置",
        "available_count": None,
        "items": []
    }
    try:
        reset_ent = parse_reset_entitlements(result, observed_at)
    except Exception:
        pass
        
    return {
        "status": rate_limits_dict["status"],
        "message": rate_limits_dict["message"],
        "items": rate_limits_dict["items"],
        "reset_entitlements": reset_ent
    }


def read_codex_app_server_quota(timeout_seconds: float = 8.0) -> dict:
    """Read the current official Codex quota through account/rateLimits/read."""
    bundled = "/Applications/ChatGPT.app/Contents/Resources/codex"
    binary = bundled if os.path.isfile(bundled) and os.access(bundled, os.X_OK) else shutil.which("codex")
    unavailable = {
        "status": "unavailable",
        "message": "暂时无法读取当前官方额度",
        "items": [],
        "reset_entitlements": {
            "status": "unavailable",
            "message": "暂时无法读取可用重置",
            "available_count": None,
            "items": []
        }
    }
    if not binary:
        return unavailable

    process = None
    try:
        process = subprocess.Popen(
            [binary, "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        initialize = {
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {"name": "antigravity-token-monitor", "version": "1.0"},
                "capabilities": {"experimentalApi": True},
            },
        }
        process.stdin.write(json.dumps(initialize, separators=(",", ":")) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + timeout_seconds
        initialized = False
        while time.monotonic() < deadline:
            ready, _, _ = select.select([process.stdout], [], [], min(0.25, max(deadline - time.monotonic(), 0)))
            if not ready:
                continue
            line = process.stdout.readline()
            if not line:
                break
            message = json.loads(line)
            if message.get("id") == 1 and isinstance(message.get("result"), dict):
                initialized = True
                break
        if not initialized:
            return unavailable

        process.stdin.write(json.dumps({"method": "initialized"}, separators=(",", ":")) + "\n")
        process.stdin.write(json.dumps({"id": 2, "method": "account/rateLimits/read", "params": None}, separators=(",", ":")) + "\n")
        process.stdin.flush()
        while time.monotonic() < deadline:
            ready, _, _ = select.select([process.stdout], [], [], min(0.25, max(deadline - time.monotonic(), 0)))
            if not ready:
                continue
            line = process.stdout.readline()
            if not line:
                break
            message = json.loads(line)
            if message.get("id") == 2:
                observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                return normalize_codex_app_server_rate_limits(message.get("result"), observed_at)
    except (OSError, ValueError, json.JSONDecodeError):
        return unavailable
    finally:
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
    return unavailable


def get_quota_status(convos, codex_calls):
    """
    Returns verified official live quota data.
    Only items with confidence == "official_live" are returned.
    """
    qstatus = {
        "antigravity": {"status": "unavailable", "message": "暂时无法读取官方额度", "items": []},
        "codex": {
            "status": "unavailable",
            "message": "暂时无法读取当前官方额度",
            "items": [],
            "reset_entitlements": {
                "status": "unavailable",
                "message": "暂时无法读取可用重置",
                "available_count": None,
                "items": []
            }
        }
    }
    
    # 1. Antigravity Quota
    try:
        qstatus["antigravity"] = read_antigravity_live_quota()
    except:
        pass
        
    # 2. Codex official app-server quota (never historical JSONL rate limits)
    try:
        qstatus["codex"] = read_codex_app_server_quota()
    except:
        pass
        
    return qstatus


def _get_aggregated_stats_unlocked():
    """Aggregates scanned conversation statistics into a lightweight summary.
    Output does NOT include conversations list or step details — only aggregated
    totals and daily series per AI source, keeping dashboard.json under 100 KB.
    """
    from datetime import date as date_cls, timedelta

    scan_result = scan_conversations()
    if len(scan_result) == 2:
        convos, scanner_stats = scan_result
        if isinstance(scanner_stats, dict) and "codex" in scanner_stats:
            codex_calls = LAST_SCAN_METADATA.get("codex_calls", [])
            codex_auth_info = LAST_SCAN_METADATA.get("codex_auth_info", {"auth_mode": "Unknown", "plan_type": "unknown_plan"})
        else:
            codex_calls, codex_auth_info = [], {"auth_mode": "Unknown", "plan_type": "unknown_plan"}
    else:
        convos, codex_calls, codex_auth_info, scanner_stats = scan_result
    settings = load_settings()
    model_prices = settings.get("model_prices", DEFAULT_SETTINGS["model_prices"])
    # Remove the earlier guessed Codex mapping/rates while preserving its
    # token and call totals under the observed raw model.
    pricing_changed = False
    for legacy_key in ("gpt-5.3-codex",):
        if legacy_key in model_prices:
            model_prices.setdefault("codex-auto-review", {
                "display_name": "Codex Auto Review", "provider": "OpenAI",
                "input_price_per_million": 0.0, "cached_input_price_per_million": 0.0,
                "output_price_per_million": 0.0, "pricing_unit": "credits",
                "pricing_profile": "unmapped", "pricing_source": "unmapped",
                "pricing_verified_at": datetime.now().strftime("%Y-%m-%d"),
                "user_overridden": False, "actual_extra_charge_confirmed": False,
                "raw_model_id": "codex-auto-review"})
            del model_prices[legacy_key]
            pricing_changed = True
    for key in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5", "gpt-5.4", "gpt-5.4-mini"):
        if key in model_prices and not model_prices[key].get("user_overridden", False):
            official = DEFAULT_SETTINGS["model_prices"].get(key)
            if official and model_prices[key] != official:
                model_prices[key] = dict(official)
                pricing_changed = True
    if "codex-auto-review" in model_prices and not model_prices["codex-auto-review"].get("user_overridden", False):
        p = model_prices["codex-auto-review"]
        if p.get("input_price_per_million", 0) != 0 or p.get("output_price_per_million", 0) != 0 or p.get("pricing_profile") != "unpriced":
            p.update({"input_price_per_million": 0.0, "cached_input_price_per_million": 0.0,
                      "output_price_per_million": 0.0, "pricing_profile": "unpriced",
                      "pricing_source": "unpriced"})
            pricing_changed = True
    if pricing_changed:
        settings["model_prices"] = model_prices
        save_settings(settings)

    today_str   = datetime.now().strftime("%Y-%m-%d")
    today_dt    = date_cls.today()
    day7_cutoff = (today_dt - timedelta(days=6)).strftime("%Y-%m-%d")
    day30_cutoff = (today_dt - timedelta(days=29)).strftime("%Y-%m-%d")

    # ──────────────────────────────────────────────
    # daily_history.json：永久账本 (v4 schema: per-model)
    # ──────────────────────────────────────────────
    daily_history_path = os.path.join(DATA_DIR, "daily_history.json")
    daily_history = _safe_load_json(daily_history_path, {"version": 4, "updated_at": "", "seen_call_ids": {}, "codex_seen_call_ids": {}, "days": {}})
    
    if "seen_call_ids" not in daily_history:
        daily_history["seen_call_ids"] = {}
    if "codex_seen_call_ids" not in daily_history:
        daily_history["codex_seen_call_ids"] = {}
    if "days" not in daily_history:
        daily_history["days"] = {}

    # Migrate the previous guessed normalized key without changing any totals.
    for day_data in daily_history.get("days", {}).values():
        models = day_data.get("sources", {}).get("codex", {}).get("models", {})
        if "gpt-5.3-codex" in models:
            old = models.pop("gpt-5.3-codex")
            target = models.setdefault("codex-auto-review", {})
            for field in ("input_tokens", "cached_input_tokens", "output_tokens",
                          "reasoning_output_tokens", "call_count"):
                target[field] = target.get(field, 0) + old.get(field, 0)
            pricing_changed = True
        
    # Schema Migration: v3 -> v4
    old_version = daily_history.get("version", 3)
    if old_version < 4:
        new_days = {}
        for d, day_data in daily_history.get("days", {}).items():
            if "sources" in day_data:
                new_days[d] = day_data
                continue
            old_ag = day_data.get("antigravity", {})
            new_days[d] = {
                "sources": {
                    "antigravity": {
                        "models": {
                            "unknown_legacy": {
                                "input_tokens":   int(old_ag.get("user_input_tokens", old_ag.get("input_tokens", 0))),
                                "output_tokens":  int(old_ag.get("output_tokens", 0)),
                                "estimated_cost": float(old_ag.get("estimated_cost", 0.0)),
                                "call_count":     0
                            }
                        }
                    }
                }
            }
        daily_history["days"] = new_days
        daily_history["version"] = 4

    seen_calls = daily_history["seen_call_ids"]
    codex_seen = daily_history["codex_seen_call_ids"]
    history_changed = False
    
    # 1. Merge current Antigravity calls
    for cid, data in convos.items():
        d = data["local_date"] or "未知"
        if d == "未知":
            continue
        if d not in daily_history["days"]:
            daily_history["days"][d] = {"sources": {"antigravity": {"models": {}}, "codex": {"models": {}}}}
        
        sources = daily_history["days"][d].setdefault("sources", {})
        ag_src = sources.setdefault("antigravity", {})
        models_dict = ag_src.setdefault("models", {})
        
        for call in data.get("model_calls", []):
            call_id = call["call_id"]
            mid = call["normalized_model_id"]
            
            if call_id not in seen_calls:
                history_changed = True
                seen_calls[call_id] = True
                if mid not in models_dict:
                    models_dict[mid] = {
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "estimated_cost": 0.0,
                        "call_count": 0
                    }
                
                m_entry = models_dict[mid]
                m_entry["input_tokens"] += call["input_tokens"]
                m_entry["output_tokens"] += call["output_tokens"]
                if mid != "unknown_legacy":
                    m_entry["call_count"] += 1
                if mid == "gemini-3.1-pro":
                    threshold = int(model_prices.get(mid, {}).get("threshold_tokens", 200000))
                    bucket = "standard" if int(call.get("input_tokens", 0)) <= threshold else "long_context"
                    breakdown = m_entry.setdefault("pricing_breakdown", {})
                    b = breakdown.setdefault(bucket, {"input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0})
                    b["input_tokens"] += int(call.get("input_tokens", 0))
                    b["output_tokens"] += int(call.get("output_tokens", 0))
                    b["estimated_cost"] += float(cost_for_call(mid, call.get("input_tokens", 0), 0, call.get("output_tokens", 0), model_prices))

    # 2. Merge current Codex calls
    for call in codex_calls:
        d = call.get("local_date") or to_local_date(call.get("timestamp", ""))
        if d == "未知":
            continue
            
        if d not in daily_history["days"]:
            daily_history["days"][d] = {"sources": {"antigravity": {"models": {}}, "codex": {"models": {}}}}
            
        sources = daily_history["days"][d].setdefault("sources", {})
        codex_src = sources.setdefault("codex", {})
        models_dict = codex_src.setdefault("models", {})
        
        call_id = call["call_id"]
        mid = call["normalized_model_id"]
        
        if call_id not in codex_seen:
            history_changed = True
            codex_seen[call_id] = True
            if mid not in models_dict:
                models_dict[mid] = {
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "uncached_input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_output_tokens": 0,
                    "estimated_cost": 0.0,
                    "call_count": 0
                }
            
            m_entry = models_dict[mid]
            m_entry["input_tokens"] = m_entry.get("input_tokens", 0) + call["input_tokens"]
            m_entry["cached_input_tokens"] = m_entry.get("cached_input_tokens", 0) + call["cached_input_tokens"]
            m_entry["output_tokens"] = m_entry.get("output_tokens", 0) + call["output_tokens"]
            m_entry["reasoning_output_tokens"] = m_entry.get("reasoning_output_tokens", 0) + call["reasoning_output_tokens"]
            m_entry["call_count"] = m_entry.get("call_count", 0) + 1

    # Recalculate estimated_cost for all entries in daily_history dynamically using current prices
    for d, d_data in daily_history.get("days", {}).items():
        # Antigravity cost
        ag_models = d_data.get("sources", {}).get("antigravity", {}).get("models", {})
        for mid, m_entry in ag_models.items():
            inp = m_entry.get("input_tokens", 0)
            cached = m_entry.get("cached_input_tokens", 0)
            out = m_entry.get("output_tokens", 0)
            
            if mid == "gemini-3.1-pro" and m_entry.get("pricing_breakdown"):
                cost_dec = sum((Decimal(str(v.get("estimated_cost", 0.0))) for v in m_entry["pricing_breakdown"].values()), Decimal("0"))
            else:
                cost_dec = cost_for_call(mid, inp, cached, out, model_prices)
            
            m_entry["estimated_cost"] = float(round(cost_dec, 9))
            
        # Codex cost/credits
        codex_models = d_data.get("sources", {}).get("codex", {}).get("models", {})
        for mid, m_entry in codex_models.items():
            inp = m_entry.get("input_tokens", 0)
            cached = m_entry.get("cached_input_tokens", 0)
            out = m_entry.get("output_tokens", 0)
            
            uncached = max(inp - cached, 0)
            m_entry["uncached_input_tokens"] = uncached
            
            p_info = model_prices.get(mid, {})
            in_rate = p_info.get("input_price_per_million", 0.0)
            cached_rate = p_info.get("cached_input_price_per_million", 0.0)
            out_rate = p_info.get("output_price_per_million", 0.0)
            
            credits_dec = (Decimal(uncached) * Decimal(str(in_rate)) / Decimal("1000000") +
                           Decimal(cached) * Decimal(str(cached_rate)) / Decimal("1000000") +
                           Decimal(out) * Decimal(str(out_rate)) / Decimal("1000000"))
            
            m_entry["estimated_cost"] = float(round(credits_dec, 9))

    # Save daily history
    if history_changed or not daily_history.get("updated_at"):
        daily_history["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Credits are rebuildable from settings. A pricing-only refresh must not
    # rewrite the accepted historical ledger or alter its audit hash.
    if history_changed or DATA_DIR != os.path.join(PROJECT_ROOT, "data"):
        _atomic_write_json(daily_history_path, daily_history)

    # ── Read back daily_history.json to produce clean aggregated dashboard stats ──
    daily_aggregated = {}
    
    for d, day_data in daily_history["days"].items():
        daily_aggregated[d] = {}
        for src_name in ["antigravity", "codex"]:
            src_day = day_data.get("sources", {}).get(src_name, {})
            models_dict = src_day.get("models", {})
            
            total_inp = 0
            total_cached = 0
            total_out = 0
            total_reasoning = 0
            total_priced = 0
            total_unpriced = 0
            models_summary = {}
            
            for mid, m_entry in models_dict.items():
                # Historical Antigravity ledgers may contain the raw alias
                # gemini-default. Keep the ledger untouched, but expose one
                # canonical model in every dashboard range.
                summary_mid = normalize_antigravity_model(mid) if src_name == "antigravity" else mid
                inp = m_entry.get("input_tokens", 0)
                cached = m_entry.get("cached_input_tokens", 0)
                out = m_entry.get("output_tokens", 0)
                reasoning = m_entry.get("reasoning_output_tokens", 0)
                recognizable = inp + out
                
                total_inp += inp
                total_cached += cached
                total_out += out
                total_reasoning += reasoning
                
                # Recalculate cost / credits dynamically
                uncached = max(inp - cached, 0)
                if src_name == "antigravity" and summary_mid == "gemini-3.1-pro" and m_entry.get("pricing_breakdown"):
                    cost_dec = sum((Decimal(str(v.get("estimated_cost", 0.0))) for v in m_entry["pricing_breakdown"].values()), Decimal("0"))
                else:
                    cost_dec = cost_for_call(summary_mid, inp, cached, out, model_prices)
                is_priced = is_priced_model(summary_mid, model_prices)
                priced_tokens = recognizable if is_priced else 0
                unpriced_tokens = recognizable - priced_tokens
                total_priced += priced_tokens
                total_unpriced += unpriced_tokens
                
                model_summary = {
                    "user_input_tokens":   inp,
                    "cached_input_tokens": cached,
                    "uncached_input_tokens": max(inp - cached, 0) if src_name == "codex" else inp,
                    "output_tokens":       out,
                    "reasoning_output_tokens": reasoning,
                    "identifiable_tokens": inp + out,
                    "priced_tokens": priced_tokens,
                    "unpriced_tokens": unpriced_tokens,
                    "estimated_cost":      float(round(cost_dec, 9)),
                    "call_count":          m_entry.get("call_count", 0)
                }
                if m_entry.get("pricing_breakdown"):
                    model_summary["pricing_breakdown"] = m_entry["pricing_breakdown"]

                if summary_mid in models_summary:
                    existing = models_summary[summary_mid]
                    for field in ("user_input_tokens", "cached_input_tokens", "output_tokens",
                                  "reasoning_output_tokens", "identifiable_tokens", "priced_tokens",
                                  "unpriced_tokens", "estimated_cost", "call_count"):
                        existing[field] = existing.get(field, 0) + model_summary.get(field, 0)
                    if "pricing_breakdown" in model_summary:
                        breakdown = existing.setdefault("pricing_breakdown", {})
                        for tier, tier_entry in model_summary["pricing_breakdown"].items():
                            if tier not in breakdown:
                                breakdown[tier] = dict(tier_entry)
                            else:
                                for key in ("input_tokens", "cached_input_tokens", "output_tokens", "estimated_cost"):
                                    breakdown[tier][key] = breakdown[tier].get(key, 0) + tier_entry.get(key, 0)
                else:
                    models_summary[summary_mid] = model_summary
                
            total_cost_dec = Decimal("0.0")
            for mid, m_sum in models_summary.items():
                total_cost_dec += Decimal(str(m_sum["estimated_cost"]))
                
            daily_aggregated[d][src_name] = {
                "user_input_tokens":   total_inp,
                "cached_input_tokens": total_cached,
                "uncached_input_tokens": max(total_inp - total_cached, 0) if src_name == "codex" else total_inp,
                "output_tokens":       total_out,
                "reasoning_output_tokens": total_reasoning,
                "identifiable_tokens": total_inp + total_out,
                "priced_tokens": total_priced,
                "unpriced_tokens": total_unpriced,
                "estimated_cost":      float(round(total_cost_dec, 9)),
                "models":              models_summary
            }

    def _sum_range_v4(cutoff, src_name):
        """Sum metrics from daily_aggregated for all dates >= cutoff for a specific source."""
        u_inp = cached = out = reasoning = ident = 0
        models_sums = {}
        
        for d, day_data in daily_aggregated.items():
            if cutoff and d < cutoff:
                continue
            src_data = day_data.get(src_name, {})
            if not src_data:
                continue
            u_inp += src_data["user_input_tokens"]
            cached += src_data.get("cached_input_tokens", 0)
            out += src_data["output_tokens"]
            reasoning += src_data.get("reasoning_output_tokens", 0)
            ident += src_data["identifiable_tokens"]
            
            for mid, m_entry in src_data.get("models", {}).items():
                if mid not in models_sums:
                    models_sums[mid] = {
                        "user_input_tokens": 0,
                        "cached_input_tokens": 0,
                        "uncached_input_tokens": 0,
                        "output_tokens": 0,
                        "reasoning_output_tokens": 0,
                        "identifiable_tokens": 0,
                        "priced_tokens": 0,
                        "unpriced_tokens": 0,
                        "estimated_cost": 0.0,
                        "call_count": 0
                    }
                    if m_entry.get("pricing_breakdown"):
                        models_sums[mid]["pricing_breakdown"] = {}
                models_sums[mid]["user_input_tokens"] += m_entry["user_input_tokens"]
                models_sums[mid]["cached_input_tokens"] += m_entry.get("cached_input_tokens", 0)
                models_sums[mid]["uncached_input_tokens"] += m_entry.get("uncached_input_tokens", 0)
                models_sums[mid]["output_tokens"] += m_entry["output_tokens"]
                models_sums[mid]["reasoning_output_tokens"] += m_entry.get("reasoning_output_tokens", 0)
                models_sums[mid]["identifiable_tokens"] += m_entry["identifiable_tokens"]
                models_sums[mid]["priced_tokens"] += m_entry.get("priced_tokens", 0)
                models_sums[mid]["unpriced_tokens"] += m_entry.get("unpriced_tokens", 0)
                models_sums[mid]["call_count"] += m_entry.get("call_count", 0)
                if m_entry.get("pricing_breakdown"):
                    target_breakdown = models_sums[mid].setdefault("pricing_breakdown", {})
                    for bucket, values in m_entry["pricing_breakdown"].items():
                        target = target_breakdown.setdefault(bucket, {"input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0})
                        target["input_tokens"] += values.get("input_tokens", 0)
                        target["output_tokens"] += values.get("output_tokens", 0)
                        target["estimated_cost"] += values.get("estimated_cost", 0.0)
                
        total_cost_dec = Decimal("0.0")
        for mid, m_sum in models_sums.items():
            inp = m_sum["user_input_tokens"]
            cached_inp = m_sum["cached_input_tokens"]
            out_tokens = m_sum["output_tokens"]
            if mid == "gemini-3.1-pro" and m_sum.get("pricing_breakdown"):
                cost_dec = sum((Decimal(str(v.get("estimated_cost", 0.0))) for v in m_sum["pricing_breakdown"].values()), Decimal("0"))
            else:
                cost_dec = cost_for_call(mid, inp, cached_inp, out_tokens, model_prices)
            
            m_sum["estimated_cost"] = float(round(cost_dec, 9))
            total_cost_dec += Decimal(str(m_sum["estimated_cost"]))
            
        return {
            "user_input_tokens":   int(u_inp),
            "cached_input_tokens": int(cached),
            "uncached_input_tokens": int(max(u_inp - cached, 0)) if src_name == "codex" else int(u_inp),
            "output_tokens":       int(out),
            "reasoning_output_tokens": int(reasoning),
            "identifiable_tokens": int(ident),
            "priced_tokens": int(sum(m.get("priced_tokens", 0) for m in models_sums.values())),
            "unpriced_tokens": int(sum(m.get("unpriced_tokens", 0) for m in models_sums.values())),
            "estimated_cost":      float(round(total_cost_dec, 9)),
            "models":              models_sums
        }

    # ── Continuous series helpers ──────────────────────────────────────────
    def _continuous_series(start_str, end_str=None, include_models=True):
        """Generate continuous daily entries with 0-fill for missing dates."""
        from datetime import date as date_cls2, timedelta
        start_dt = date_cls2.fromisoformat(start_str)
        end_dt   = date_cls2.today() if end_str is None else date_cls2.fromisoformat(end_str)
        out_list = []
        cur = start_dt
        while cur <= end_dt:
            ds = cur.strftime("%Y-%m-%d")
            day_data = daily_aggregated.get(ds, {})
            
            sources_summary = {}
            for src_name in ["antigravity", "codex"]:
                src_day = day_data.get(src_name, {
                    "user_input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "reasoning_output_tokens": 0, "identifiable_tokens": 0, "models": {}
                })
                models_dict = src_day.get("models", {})
                
                models_summary = {}
                if include_models:
                    for mid, m_entry in models_dict.items():
                        models_summary[mid] = {
                            "user_input_tokens":   m_entry["user_input_tokens"],
                            "cached_input_tokens": m_entry.get("cached_input_tokens", 0),
                            "output_tokens":       m_entry["output_tokens"],
                            "reasoning_output_tokens": m_entry.get("reasoning_output_tokens", 0),
                            "identifiable_tokens": m_entry["identifiable_tokens"]
                        }
                    
                sources_summary[src_name] = {
                    "user_input_tokens":   src_day["user_input_tokens"],
                    "output_tokens":       src_day["output_tokens"],
                    "identifiable_tokens": src_day["identifiable_tokens"]
                }
                
            out_list.append({
                "date": ds,
                "sources": sources_summary
            })
            cur += timedelta(days=1)
        return out_list

    last_7_series  = _continuous_series(day7_cutoff, include_models=True)
    last_30_series = _continuous_series(day30_cutoff, include_models=False)
    if daily_aggregated:
        earliest = min(daily_aggregated.keys())
        all_series = _continuous_series(earliest, include_models=False)
    else:
        all_series = []

    today_has_hourly = False

    result = {
        "last_scan_time":    scanner_stats["last_scan_time"],
        "scan_duration_ms":  scanner_stats["scan_duration_ms"],
        "today_has_hourly":  today_has_hourly,
        "sources": {
            "antigravity": {
                "today":    _sum_range_v4(today_str, "antigravity"),
                "last_7":   _sum_range_v4(day7_cutoff, "antigravity"),
                "last_30":  _sum_range_v4(day30_cutoff, "antigravity"),
                "all_time": _sum_range_v4(None, "antigravity")
            },
            "codex": {
                "today":    _sum_range_v4(today_str, "codex"),
                "last_7":   _sum_range_v4(day7_cutoff, "codex"),
                "last_30":  _sum_range_v4(day30_cutoff, "codex"),
                "all_time": _sum_range_v4(None, "codex")
            }
        },
        "last_7_series":  last_7_series,
        "last_30_series": last_30_series,
        "all_series":     all_series,
        "codex_auth_info": codex_auth_info,
        "scanner_stats":  scanner_stats,
        "quota_events":   scan_quota_events(),
        "quota_status":   get_quota_status(convos, codex_calls),
        "pricing_tier":   settings.get("pricing_tier", "standard"),
    }

    # Keep the compact artifact byte-for-byte stable on a no-op rescan. The
    # volatile scan timestamp/duration are still refreshed whenever statistics
    # actually change.
    previous_dashboard = _safe_load_json(os.path.join(DATA_DIR, "dashboard.json"), {})
    if codex_auth_info.get("plan_type") == "unknown_plan":
        previous_auth = previous_dashboard.get("codex_auth_info", {})
        if previous_auth.get("plan_type") not in (None, "unknown_plan"):
            codex_auth_info = dict(previous_auth)
            result["codex_auth_info"] = codex_auth_info
    # A successful scan always receives a fresh valid ISO timestamp. The
    # aggregated ranges remain independent of today's range.

    # convo_list is still needed for history accounting — never written to dashboard
    convo_list = []
    for cid, data in convos.items():
        convo_list.append({
            "id":         cid,
            "title":      data.get("title", ""),
            "last_active": data.get("last_active", ""),
            "steps_count": data.get("steps_count", 0),
            "original_tokens":           data.get("original_tokens", 0),
            "accumulated_context_tokens": data.get("accumulated_context_tokens", 0),
            "assistant_output_tokens":    data.get("assistant_output_tokens", 0),
            "original_categories":        data.get("original_categories", {}),
            "cost":                       data.get("cost", 0.0),
        })

    # 保存结果至项目本地的 dashboard.json（原子写入）
    dashboard_path = os.path.join(DATA_DIR, "dashboard.json")
    _atomic_write_json(dashboard_path, result)

    # ──────────────────────────────────────────────
    # conversation_history.json：对话级永久摘要账本
    # ──────────────────────────────────────────────
    conv_history_path = os.path.join(DATA_DIR, "conversation_history.json")
    conv_history = _safe_load_json(conv_history_path, {"version": 1, "updated_at": "", "conversations": {}})
    if "conversations" not in conv_history:
        conv_history["conversations"] = {}

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    active_ids = set()

    for item in convo_list:
        cid = item["id"]
        active_ids.add(cid)
        prev = conv_history["conversations"].get(cid, {})
        conv_history["conversations"][cid] = {
            "id":                  cid,
            "title":               item["title"] or prev.get("title", ""),
            "first_seen":          prev.get("first_seen", now_str),
            "last_seen":           now_str,
            "last_active":         item.get("last_active") or prev.get("last_active", ""),
            "step_count":          max(prev.get("step_count", 0), item.get("steps_count", 0)),
            "raw_tokens":          max(prev.get("raw_tokens", 0), item.get("original_tokens", 0)),
            "accumulated_context": max(prev.get("accumulated_context", 0), item.get("accumulated_context_tokens", 0)),
            "output_tokens":       max(prev.get("output_tokens", 0), item.get("assistant_output_tokens", 0)),
            "estimated_cost":      item.get("cost", 0.0),
            "status":              "active",
            "source_path":         cid,
            "snapshot_only":       False
        }

    # 将本次扫描不到的历史对话标记为 archived（不删除）
    for cid, entry in conv_history["conversations"].items():
        if cid not in active_ids and entry.get("status") == "active":
            conv_history["conversations"][cid]["status"] = "archived"
            conv_history["conversations"][cid]["snapshot_only"] = True

    conv_history["updated_at"] = now_str
    _atomic_write_json(conv_history_path, conv_history)

    return result


def get_aggregated_stats():
    """Run one complete scan while holding the process-wide filesystem lock."""
    with scan_lock():
        return _get_aggregated_stats_unlocked()


def _atomic_write_json(path: str, data: dict):
    """原子写入 JSON：先写临时文件，fsync，再 rename 替换，出错时保留 .bak。"""
    import sys, tempfile
    backup_path = path + ".bak"
    tmp_path = path + ".tmp"
    try:
        # 若旧文件存在，先备份
        if os.path.exists(path):
            try:
                import shutil
                shutil.copy2(path, backup_path)
            except Exception:
                pass

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)
    except Exception as e:
        print(f"警告: 原子写入 {path} 失败: {e}", file=sys.stderr)


def _safe_load_json(path: str, default: dict) -> dict:
    """安全读取 JSON，损坏时尝试读取 .bak，否则返回 default。"""
    backup_path = path + ".bak"
    for target in [path, backup_path]:
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return dict(default)


if __name__ == "__main__":
    try:
        print("正在扫描本地 Antigravity 对话日志...")
        stats = get_aggregated_stats()
        ag = stats["sources"]["antigravity"]
        t = ag["today"]
        print(f"今日  用户输入: {t['user_input_tokens']:,}  输出: {t['output_tokens']:,}  可识别: {t['identifiable_tokens']:,}")
        print(f"7 天  总可识别: {ag['last_7']['identifiable_tokens']:,}  费用: ${ag['last_7']['estimated_cost']:.4f}")
        print(f"30 天 总可识别: {ag['last_30']['identifiable_tokens']:,}")
        print(f"累计  总可识别: {ag['all_time']['identifiable_tokens']:,}  费用: ${ag['all_time']['estimated_cost']:.4f}")
        print(f"7日连续序列长度:  {len(stats['last_7_series'])}（应为 7）")
        print(f"30日连续序列长度: {len(stats['last_30_series'])}（应为 30）")
        print(f"扫描耗时: {stats['scan_duration_ms']} ms")
    except ScanBusyError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(75)
    except Exception as exc:
        print(f"扫描失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
