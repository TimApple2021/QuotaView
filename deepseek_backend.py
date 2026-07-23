"""DeepSeek API usage management module for QuotaView.

Provides:
1. DeepSeek official usage ZIP import parser (amount-*.csv & cost-*.csv)
2. Atomic persistence for DeepSeek usage history
3. Dashboard snapshot generator (reads deepseek_balance_cache.json & deepseek_usage_history.json)

Note: Keychain storage and live balance API requests are handled natively in Swift (Security.framework & URLSession).
Python code contains zero subprocess security calls and zero network calls to the DeepSeek API.
"""

import csv
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

MAX_ZIP_FILES = 50
MAX_UNCOMPRESSED_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit


# ---------------------------------------------------------------------------
# Atomic File Persistence & Locking Helpers
# ---------------------------------------------------------------------------

def _atomic_write_json(path: str, data: dict):
    """Atomically writes dictionary to JSON file with .bak backup and fsync."""
    dir_name = os.path.dirname(os.path.abspath(path))
    os.makedirs(dir_name, exist_ok=True)
    base_name = os.path.basename(path)
    tmp_path = os.path.join(dir_name, f".{base_name}.tmp")
    backup_path = path + ".bak"

    try:
        if os.path.exists(path):
            try:
                shutil.copy2(path, backup_path)
            except Exception:
                pass

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, path)
    except Exception as e:
        print(f"警告: DeepSeek 原子写入 {path} 失败: {e}", file=sys.stderr)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass


def _safe_load_json(path: str, default: dict) -> dict:
    """Safely loads JSON. If primary file corrupt, attempts .bak backup."""
    backup_path = path + ".bak"
    for target in [path, backup_path]:
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return dict(default)


class DeepSeekLock:
    """Inter-process lock for DeepSeek history operations."""
    def __init__(self, data_dir: str):
        self.lock_path = os.path.join(data_dir, "deepseek.lock")
        self.fd = None

    def __enter__(self):
        os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
        try:
            self.fd = open(self.lock_path, "w")
            fcntl.flock(self.fd, fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass


def mask_api_key(key: str) -> str:
    """Returns masked version of API key for display, e.g. sk-****1234."""
    if not key:
        return "未配置"
    key = key.strip()
    if len(key) <= 8:
        return f"{key[:2]}****{key[-2:]}"
    return f"{key[:4]}****{key[-4:]}"


def _get_stable_key_identifier(api_key_raw: str, api_key_name: str) -> str:
    """Legacy raw-key fingerprint retained only for compatibility matching."""
    clean_key = (api_key_raw or "").strip()
    if clean_key:
        return hashlib.sha256(clean_key.encode("utf-8")).hexdigest()[:16]
    return ""


def _canonical_key_id(user_id: str, api_key_masked: str, legacy_stable_key_hash: str = "") -> str:
    """Return a non-displayable identity independent of the mutable key name."""
    user = str(user_id or "").strip()
    masked = str(api_key_masked or "").strip().lower()
    if user and masked:
        payload = f"{user}|{masked}"
    elif legacy_stable_key_hash:
        payload = f"legacy|{legacy_stable_key_hash}"
    else:
        payload = f"anonymous|{masked}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# DeepSeek Usage ZIP Importer & CSV Parser
# ---------------------------------------------------------------------------

def _normalize_utc_date(raw_date: str) -> str:
    """Converts 20310105 or 2031-01-05 into standard YYYY-MM-DD."""
    clean = re.sub(r"[^\d]", "", str(raw_date or "").strip())
    if len(clean) == 8:
        return f"{clean[:4]}-{clean[4:6]}-{clean[6:8]}"
    if len(clean) == 10 and clean.count("-") == 2:
        return clean
    return str(raw_date or "").strip()


def parse_deepseek_csv_contents(amount_csv_text: str, cost_csv_text: str = None) -> dict:
    """Parses amount and cost CSV string contents into normalized usage records."""
    warnings = []

    # 1. Parse cost CSV for currency and wallet_type per (date, model)
    model_date_cost_map = {}
    if cost_csv_text:
        reader = csv.DictReader(io.StringIO(cost_csv_text))
        for row in reader:
            dt = _normalize_utc_date(row.get("utc_date") or row.get("date") or "")
            model_id = str(row.get("model") or "unknown").strip()
            curr = str(row.get("currency") or "CNY").strip().upper()
            wallet_type = str(row.get("wallet_type") or "Paid").strip()
            cost_val_str = str(row.get("cost") or "0").strip()

            if dt and model_id:
                key = (dt, model_id)
                if key not in model_date_cost_map:
                    model_date_cost_map[key] = {
                        "currency": curr,
                        "wallet_type": wallet_type,
                        "cost": Decimal("0.000000"),
                    }
                try:
                    model_date_cost_map[key]["cost"] += Decimal(cost_val_str)
                except (InvalidOperation, TypeError):
                    pass

    # 2. Parse amount CSV
    reader = csv.DictReader(io.StringIO(amount_csv_text))
    fieldnames = reader.fieldnames or []

    has_amount = any("amount" in fn.lower() for fn in fieldnames)
    has_type = any("type" in fn.lower() for fn in fieldnames)
    if not (has_amount and has_type):
        raise ValueError("导出 CSV 缺少必要的 amount 或 type 列")

    grouped = {}

    for row in reader:
        raw_date = row.get("utc_date") or row.get("date") or ""
        dt = _normalize_utc_date(raw_date)
        if not dt:
            continue

        model_id = str(row.get("model") or "unknown").strip()
        user_id = str(row.get("user_id") or row.get("uid") or "").strip()
        api_key_name = str(row.get("api_key_name") or row.get("key_name") or "默认").strip()
        raw_api_key = str(row.get("api_key") or "").strip()
        key_masked = mask_api_key(raw_api_key) if raw_api_key else api_key_name
        stable_key_hash = _get_stable_key_identifier(raw_api_key, api_key_name)
        canonical_key_id = _canonical_key_id(user_id, key_masked, stable_key_hash)

        cost_info = model_date_cost_map.get((dt, model_id), {})
        currency = cost_info.get("currency", "CNY")
        wallet_type = cost_info.get("wallet_type", "Paid")

        m_type = str(row.get("type") or "").strip()
        price_str = str(row.get("price") or "").strip()
        amount_str = str(row.get("amount") or "").strip()

        group_key = (dt, model_id, canonical_key_id, currency, wallet_type)
        if group_key not in grouped:
            grouped[group_key] = {
                "date": dt,
                "model_id": model_id,
                "user_id": user_id,
                "api_key_name": api_key_name,
                "api_key_masked": key_masked,
                "stable_key_hash": stable_key_hash,
                "canonical_key_id": canonical_key_id,
                "wallet_type": wallet_type,
                "request_count": 0,
                "cache_hit_input_tokens": 0,
                "cache_miss_input_tokens": 0,
                "output_tokens": 0,
                "actual_amount": Decimal("0.000000"),
                "currency": currency,
            }

        rec = grouped[group_key]
        rec["user_id"] = user_id or rec.get("user_id", "")
        rec["api_key_name"] = api_key_name
        rec["api_key_masked"] = key_masked

        try:
            amount_num = max(0, int(float(amount_str))) if amount_str else 0
        except ValueError:
            amount_num = 0

        if m_type == "request_count":
            rec["request_count"] += amount_num
        elif m_type == "input_cache_hit_tokens":
            rec["cache_hit_input_tokens"] += amount_num
        elif m_type == "input_cache_miss_tokens":
            rec["cache_miss_input_tokens"] += amount_num
        elif m_type == "output_tokens":
            rec["output_tokens"] += amount_num

        if price_str and amount_str:
            try:
                p_dec = max(Decimal("0"), Decimal(price_str))
                a_dec = max(Decimal("0"), Decimal(amount_str))
                rec["actual_amount"] += (p_dec * a_dec)
            except (InvalidOperation, TypeError, ValueError):
                pass

    # 3. Build normalized deterministic records & validate against cost CSV
    normalized_records = {}
    dates = []
    currencies = set()
    model_amount_sums = {}

    for (dt, model_id, canonical_key_id, currency, wallet_type), rec in grouped.items():
        input_tokens = rec["cache_hit_input_tokens"] + rec["cache_miss_input_tokens"]
        output_tokens = rec["output_tokens"]
        total_tokens = input_tokens + output_tokens

        natural_key = f"{dt}|{model_id}|{canonical_key_id}|{rec['currency']}|{rec['wallet_type']}"
        rec_id = f"ds_rec_{hashlib.sha256(natural_key.encode('utf-8')).hexdigest()[:16]}"

        dates.append(dt)
        currencies.add(rec["currency"])

        model_key = (dt, model_id)
        model_amount_sums[model_key] = model_amount_sums.get(model_key, Decimal("0.000000")) + rec["actual_amount"]

        normalized_records[rec_id] = {
            "date": dt,
            "model_id": model_id,
            "user_id": rec["user_id"],
            "api_key_name": rec["api_key_name"],
            "api_key_masked": rec["api_key_masked"],
            "stable_key_hash": rec["stable_key_hash"],
            "canonical_key_id": canonical_key_id,
            "wallet_type": rec["wallet_type"],
            "request_count": rec["request_count"],
            "cache_hit_input_tokens": rec["cache_hit_input_tokens"],
            "cache_miss_input_tokens": rec["cache_miss_input_tokens"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "actual_amount": str(rec["actual_amount"].quantize(Decimal("0.000001"))),
            "currency": rec["currency"],
            "deterministic_record_id": rec_id,
        }

    # Cross-check sum against cost CSV
    for model_key, calc_sum in model_amount_sums.items():
        if model_key in model_date_cost_map:
            cost_csv_sum = model_date_cost_map[model_key]["cost"]
            diff = abs(calc_sum - cost_csv_sum)
            if diff > Decimal("0.0001"):
                dt, mid = model_key
                warnings.append(f"日期 {dt} 模型 {mid} 的 amount 推算金额 ({calc_sum:.6f}) 与 cost 记录金额 ({cost_csv_sum:.6f}) 存在微小汇总差异")

    coverage_start = min(dates) if dates else ""
    coverage_end = max(dates) if dates else ""

    return {
        "records": normalized_records,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "currencies": sorted(list(currencies)) if currencies else ["CNY"],
        "warnings": warnings,
    }


def _record_natural_id(record: dict) -> str:
    canonical = record.get("canonical_key_id") or _canonical_key_id(
        record.get("user_id", ""),
        record.get("api_key_masked", ""),
        record.get("stable_key_hash", ""),
    )
    return "ds_rec_" + hashlib.sha256(
        "|".join([
            str(record.get("date", "")),
            str(record.get("model_id", "unknown")),
            canonical,
            str(record.get("currency", "CNY")),
            str(record.get("wallet_type", "Paid")),
        ]).encode("utf-8")
    ).hexdigest()[:16]


def _migrate_history_dict(history: dict) -> tuple[dict, bool]:
    """Normalize old records without changing their numerical totals."""
    records = history.get("normalized_records", {})
    if not isinstance(records, dict):
        records = {}
    migrated = {}
    aliases = dict(history.get("key_aliases", {}) or {})
    changed = False
    for old_id, raw in records.items():
        if not isinstance(raw, dict):
            continue
        rec = dict(raw)
        user_id = str(rec.get("user_id") or "")
        masked = str(rec.get("api_key_masked") or "")
        canonical = (_canonical_key_id(user_id, masked, rec.get("stable_key_hash", ""))
                     if user_id or masked else str(rec.get("canonical_key_id") or ""))
        rec["canonical_key_id"] = canonical
        rec["user_id"] = str(rec.get("user_id") or "")
        new_id = _record_natural_id(rec)
        if new_id != old_id or "canonical_key_id" not in raw or "user_id" not in raw:
            changed = True

        alias = str(rec.get("api_key_name") or "默认")
        alias_list = aliases.setdefault(canonical, [])
        if alias not in alias_list:
            alias_list.append(alias)

        if new_id not in migrated:
            migrated[new_id] = rec
            continue

        # A legacy name split can produce two records for the same natural row.
        # Merge numeric fields rather than creating a second historical charge.
        target = migrated[new_id]
        for field in ("request_count", "cache_hit_input_tokens", "cache_miss_input_tokens", "input_tokens", "output_tokens", "total_tokens"):
            target[field] = int(target.get(field, 0) or 0) + int(rec.get(field, 0) or 0)
        target["actual_amount"] = str(Decimal(str(target.get("actual_amount", "0"))) + Decimal(str(rec.get("actual_amount", "0"))))
        if str(rec.get("date", "")) >= str(target.get("date", "")):
            target["api_key_name"] = rec.get("api_key_name", target.get("api_key_name", "默认"))
            target["api_key_masked"] = rec.get("api_key_masked", target.get("api_key_masked", "未配置"))
        changed = True

    history["normalized_records"] = migrated
    history["key_aliases"] = aliases
    return history, changed


def migrate_deepseek_history_file(data_dir: str) -> dict:
    """Explicitly migrate an existing history file; callers decide when to write."""
    path = os.path.join(data_dir, "deepseek_usage_history.json")
    history = _safe_load_json(path, {})
    migrated, changed = _migrate_history_dict(history)
    if changed:
        _atomic_write_json(path, migrated)
    return migrated


def import_deepseek_usage_zip(zip_path: str, data_dir: str) -> dict:
    """Imports a DeepSeek official usage_data_*.zip archive safely and idempotently."""
    if not zip_path or not os.path.exists(zip_path):
        raise ValueError("ZIP 文件不存在")

    if not zip_path.lower().endswith(".zip"):
        raise ValueError("只允许导入 .zip 压缩包")

    with open(zip_path, "rb") as f:
        header = f.read(4)
        if header != b"PK\x03\x04":
            raise ValueError("非法的 ZIP 文件头格式")

    with DeepSeekLock(data_dir):
        with zipfile.ZipFile(zip_path, "r") as z:
            infolist = z.infolist()
            if len(infolist) > MAX_ZIP_FILES:
                raise ValueError(f"ZIP 包含文件过多 ({len(infolist)} > {MAX_ZIP_FILES})")

            total_uncompressed = sum(info.file_size for info in infolist)
            if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
                raise ValueError(f"ZIP 解压总体积过大 ({total_uncompressed / 1024 / 1024:.1f} MB > 50 MB)")

            with tempfile.TemporaryDirectory() as tmpdir:
                amount_csv_text = None
                cost_csv_text = None

                for info in infolist:
                    if (info.external_attr >> 16) & 0o120000 == 0o120000:
                        raise ValueError(f"禁止解压符号链接: {info.filename}")

                    target_path = os.path.abspath(os.path.join(tmpdir, info.filename))
                    if not target_path.startswith(os.path.abspath(tmpdir)):
                        raise ValueError(f"检测到非法路径穿越: {info.filename}")

                    if info.filename.endswith(".csv"):
                        raw_bytes = z.read(info.filename)
                        text = raw_bytes.decode("utf-8-sig" if raw_bytes.startswith(b"\xef\xbb\xbf") else "utf-8", errors="replace")

                        lower_name = info.filename.lower()
                        if "amount" in lower_name:
                            amount_csv_text = text
                        elif "cost" in lower_name:
                            cost_csv_text = text

                if not amount_csv_text:
                    raise ValueError("ZIP 包中未找到包含用量明细的 amount CSV 文件")

                parsed = parse_deepseek_csv_contents(amount_csv_text, cost_csv_text)

        history_path = os.path.join(data_dir, "deepseek_usage_history.json")
        history = _safe_load_json(history_path, {
            "schema_version": 1,
            "imported_files": [],
            "imported_ranges": [],
            "normalized_records": {},
            "coverage_start": "",
            "coverage_end": "",
            "last_import_at": "",
            "currencies": ["CNY"],
            "source_format_version": 1,
        })

        history, _ = _migrate_history_dict(history)
        existing_records = history.get("normalized_records", {})
        if not isinstance(existing_records, dict):
            existing_records = {}

        file_name = os.path.basename(zip_path)
        with open(zip_path, "rb") as f:
            file_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()}"

        new_records = 0
        skipped_records = 0
        total_reqs = 0
        total_in_tokens = 0
        total_out_tokens = 0
        total_amount_dec = Decimal("0.000000")
        models_set = set()
        keys_set = set()

        for parsed_id, rec in parsed["records"].items():
            rec["source_file_hash"] = file_hash
            models_set.add(rec["model_id"])
            keys_set.add(rec["api_key_name"])
            aliases = history.setdefault("key_aliases", {})
            alias_list = aliases.setdefault(str(rec.get("canonical_key_id", "")), [])
            if rec.get("api_key_name") and rec["api_key_name"] not in alias_list:
                alias_list.append(rec["api_key_name"])
            total_reqs += rec["request_count"]
            total_in_tokens += rec["input_tokens"]
            total_out_tokens += rec["output_tokens"]
            try:
                total_amount_dec += Decimal(rec["actual_amount"])
            except (InvalidOperation, TypeError):
                pass

            rec_id = parsed_id
            # Bridge a legacy record whose raw key fingerprint predates the
            # user_id + masked-key canonical identity.
            for existing_id, existing in existing_records.items():
                if not isinstance(existing, dict):
                    continue
                if (
                    existing.get("date") == rec.get("date")
                    and existing.get("model_id") == rec.get("model_id")
                    and existing.get("currency") == rec.get("currency")
                    and existing.get("wallet_type", "Paid") == rec.get("wallet_type", "Paid")
                    and existing.get("stable_key_hash")
                    and existing.get("stable_key_hash") == rec.get("stable_key_hash")
                ):
                    rec_id = existing_id
                    break

            if rec_id in existing_records and existing_records[rec_id] == rec:
                skipped_records += 1
            else:
                if rec_id not in existing_records:
                    new_records += 1
                existing_records[rec_id] = rec

        all_dates = [r["date"] for r in existing_records.values() if isinstance(r, dict) and "date" in r]
        coverage_start = min(all_dates) if all_dates else parsed["coverage_start"]
        coverage_end = max(all_dates) if all_dates else parsed["coverage_end"]

        active_currencies = sorted(list(set(r["currency"] for r in existing_records.values() if isinstance(r, dict) and "currency" in r)))

        imported_files = history.get("imported_files", [])
        if not isinstance(imported_files, list):
            imported_files = []
        if not any(item.get("file_hash") == file_hash for item in imported_files if isinstance(item, dict)):
            imported_files.append({
                "filename": file_name,
                "file_hash": file_hash,
                "imported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "date_start": parsed["coverage_start"],
                "date_end": parsed["coverage_end"],
                "record_count": len(parsed["records"]),
            })

        imported_ranges = history.get("imported_ranges", [])
        if not isinstance(imported_ranges, list):
            imported_ranges = []
        imported_ranges.append({"start": parsed["coverage_start"], "end": parsed["coverage_end"]})

        history.update({
            "schema_version": 1,
            "imported_files": imported_files,
            "imported_ranges": imported_ranges,
            "normalized_records": existing_records,
            "coverage_start": coverage_start,
            "coverage_end": coverage_end,
            "last_import_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "currencies": active_currencies if active_currencies else ["CNY"],
            "source_format_version": 1,
        })

        _atomic_write_json(history_path, history)
        update_deepseek_dashboard_snapshot(data_dir)

        return {
            "success": True,
            "file_name": file_name,
            "date_range": f"{parsed['coverage_start']} 至 {parsed['coverage_end']}" if parsed["coverage_start"] else "未知",
            "new_records": new_records,
            "skipped_records": skipped_records,
            "request_count": total_reqs,
            "input_tokens": total_in_tokens,
            "output_tokens": total_out_tokens,
            "total_tokens": total_in_tokens + total_out_tokens,
            "actual_amount": str(total_amount_dec.quantize(Decimal("0.01"))),
            "currency": parsed["currencies"][0] if parsed["currencies"] else "CNY",
            "model_count": len(models_set),
            "key_count": len(keys_set),
            "warnings": parsed.get("warnings", []),
        }


# ---------------------------------------------------------------------------
# Dashboard Snapshot Helper
# ---------------------------------------------------------------------------

def _build_usage_summary(records: dict, month: Optional[str] = None) -> dict:
    models_map, keys_map, daily_map = {}, {}, {}
    total_reqs = total_in_tokens = total_out_tokens = 0
    total_amount_dec = Decimal("0")
    key_latest = {}
    record_index = 0
    filtered_currencies = set()

    # Display metadata is global: a historical month must use the latest
    # known name for the same stable key, while its numeric totals stay local
    # to the selected month.
    global_key_names = {}
    global_key_latest = {}
    for index, rec in enumerate(records.values()):
        if not isinstance(rec, dict):
            continue
        key_id = str(rec.get("canonical_key_id") or _canonical_key_id(rec.get("user_id", ""), rec.get("api_key_masked", ""), rec.get("stable_key_hash", "")))
        candidate = (str(rec.get("date", "")), index)
        if key_id not in global_key_latest or candidate >= global_key_latest[key_id]:
            global_key_latest[key_id] = candidate
            global_key_names[key_id] = (str(rec.get("api_key_name", "默认")), str(rec.get("api_key_masked", "未配置")))

    for rec in records.values():
        record_index += 1
        if not isinstance(rec, dict):
            continue
        dt = str(rec.get("date", ""))
        if month and not dt.startswith(month + "-"):
            continue
        model_id = str(rec.get("model_id", "unknown"))
        key_id = str(rec.get("canonical_key_id") or _canonical_key_id(rec.get("user_id", ""), rec.get("api_key_masked", ""), rec.get("stable_key_hash", "")))
        key_name, key_masked = global_key_names.get(key_id, (str(rec.get("api_key_name", "默认")), str(rec.get("api_key_masked", "未配置"))))
        curr = str(rec.get("currency", "CNY"))
        filtered_currencies.add(curr)
        reqs = int(rec.get("request_count", 0) or 0)
        in_tok = int(rec.get("input_tokens", 0) or 0)
        out_tok = int(rec.get("output_tokens", 0) or 0)
        tot_tok = int(rec.get("total_tokens", in_tok + out_tok) or 0)
        try:
            amount = Decimal(str(rec.get("actual_amount", "0")))
        except (InvalidOperation, TypeError):
            amount = Decimal("0")

        total_reqs += reqs; total_in_tokens += in_tok; total_out_tokens += out_tok; total_amount_dec += amount
        model = models_map.setdefault(model_id, {"model_id": model_id, "request_count": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "actual_amount": Decimal("0"), "currency": curr})
        model["request_count"] += reqs; model["input_tokens"] += in_tok; model["output_tokens"] += out_tok; model["total_tokens"] += tot_tok; model["actual_amount"] += amount
        key = keys_map.setdefault(key_id, {"canonical_key_id": key_id, "api_key_name": key_name, "api_key_masked": key_masked, "request_count": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "actual_amount": Decimal("0"), "currency": curr})
        key["request_count"] += reqs; key["input_tokens"] += in_tok; key["output_tokens"] += out_tok; key["total_tokens"] += tot_tok; key["actual_amount"] += amount
        latest = key_latest.get(key_id)
        if latest is None or (dt, record_index) >= (latest[0], latest[1]):
            key["api_key_name"] = key_name; key["api_key_masked"] = key_masked; key_latest[key_id] = (dt, record_index)
        if dt:
            day = daily_map.setdefault(dt, {"date": dt, "request_count": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "actual_amount": Decimal("0"), "currency": curr})
            day["request_count"] += reqs; day["input_tokens"] += in_tok; day["output_tokens"] += out_tok; day["total_tokens"] += tot_tok; day["actual_amount"] += amount

    def output_items(mapping):
        out = []
        for item in mapping.values():
            out.append({k: (str(item[k].quantize(Decimal("0.01"))) if k == "actual_amount" else item[k]) for k in item})
        return sorted(out, key=lambda x: x["total_tokens"], reverse=True)

    daily_series = [{k: (str(item[k].quantize(Decimal("0.01"))) if k == "actual_amount" else item[k]) for k in item} for item in (daily_map[d] for d in sorted(daily_map))]
    dates = sorted(daily_map)
    return {
        "has_history": bool(dates),
        "coverage_start": dates[0] if dates else "",
        "coverage_end": dates[-1] if dates else "",
        "currencies": sorted(filtered_currencies) or ["CNY"],
        "total_request_count": total_reqs, "total_input_tokens": total_in_tokens, "total_output_tokens": total_out_tokens,
        "total_tokens": total_in_tokens + total_out_tokens,
        "total_actual_amount": str(total_amount_dec.quantize(Decimal("0.01"))),
        "models": output_items(models_map), "keys": output_items(keys_map), "daily_series": daily_series,
    }


def get_deepseek_dashboard_snapshot(data_dir: str) -> dict:
    """Generate DeepSeek data from local files; balance remains independent of month selection."""
    balance_cache = _safe_load_json(os.path.join(data_dir, "deepseek_balance_cache.json"), {})
    history = _safe_load_json(os.path.join(data_dir, "deepseek_usage_history.json"), {})
    records = history.get("normalized_records", {}) if isinstance(history.get("normalized_records", {}), dict) else {}
    all_usage = _build_usage_summary(records)
    months = sorted({str(r.get("date", ""))[:7] for r in records.values() if isinstance(r, dict) and re.match(r"^\d{4}-\d{2}-\d{2}$", str(r.get("date", "")))}, reverse=True)
    monthly = []
    for month in months:
        summary = _build_usage_summary(records, month)
        monthly.append({k: summary[k] for k in ("coverage_start", "coverage_end", "total_actual_amount", "total_request_count", "total_input_tokens", "total_output_tokens", "total_tokens", "models", "keys")})
        monthly[-1]["month"] = month
    is_configured = bool(balance_cache.get("configured", False))
    return {
        "balance": {
            "configured": is_configured, "is_available": bool(balance_cache.get("is_available", False)), "currency": str(balance_cache.get("currency") or "CNY"),
            "total_balance": str(balance_cache.get("total_balance") or ("0.00" if is_configured else "—")), "granted_balance": str(balance_cache.get("granted_balance") or ("0.00" if is_configured else "—")),
            "topped_up_balance": str(balance_cache.get("topped_up_balance") or ("0.00" if is_configured else "—")), "balance_infos": balance_cache.get("balance_infos", []),
            "fetched_at": str(balance_cache.get("fetched_at") or ""), "error_code": balance_cache.get("error_code"), "error_message": balance_cache.get("error_message"),
        },
        "usage": {**all_usage, "last_import_at": str(history.get("last_import_at") or ""), "available_months": months, "monthly_summaries": monthly},
    }


def update_deepseek_dashboard_snapshot(data_dir: str):
    """Updates only the 'deepseek' node inside dashboard.json atomically without full rescan."""
    dash_path = os.path.join(data_dir, "dashboard.json")
    dashboard = _safe_load_json(dash_path, {})
    if not dashboard:
        return
    snapshot = get_deepseek_dashboard_snapshot(data_dir)
    dashboard["deepseek"] = snapshot
    _atomic_write_json(dash_path, dashboard)
