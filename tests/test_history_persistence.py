"""
tests/test_history_persistence.py
专项测试：daily_history.json 永久账本机制 (v2 schema: per-source input/output)
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOKEN_MONITOR_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TOKEN_MONITOR_DIR))

import monitor_backend

INPUT_PRICE  = 0.075   # per million
OUTPUT_PRICE = 0.30    # per million

def _cost(inp, out):
    return round((inp * INPUT_PRICE + out * OUTPUT_PRICE) / 1_000_000, 6)


class TestDailyHistoryPersistence(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.hist_path = os.path.join(self.tmpdir, "daily_history.json")
        self.bak_path  = self.hist_path + ".bak"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── 1. 首次创建 ──────────────────────────────────────────────────────
    def test_01_first_creation(self):
        self.assertFalse(os.path.exists(self.hist_path))
        h = self._run_merge({"2026-07-01": {"input_tokens": 100, "output_tokens": 50}})
        self.assertIn("2026-07-01", h["days"])
        self.assertEqual(h["days"]["2026-07-01"]["antigravity"]["input_tokens"], 100)

    # ── 2. 同一天两次扫描不翻倍 ──────────────────────────────────────────
    def test_02_no_doubling_on_rescan(self):
        daily = {"2026-07-10": {"input_tokens": 500, "output_tokens": 200}}
        self._run_merge(daily)
        h = self._run_merge(daily)
        self.assertEqual(h["days"]["2026-07-10"]["antigravity"]["input_tokens"], 500)

    # ── 3. 当前值变大时正确更新 ───────────────────────────────────────────
    def test_03_larger_value_updates(self):
        self._run_merge({"2026-07-11": {"input_tokens": 100, "output_tokens": 40}})
        h = self._run_merge({"2026-07-11": {"input_tokens": 999, "output_tokens": 400}})
        self.assertEqual(h["days"]["2026-07-11"]["antigravity"]["input_tokens"], 999)

    # ── 4. 当前值变小时保留旧值 ────────────────────────────────────────────
    def test_04_smaller_value_keeps_old(self):
        self._run_merge({"2026-07-12": {"input_tokens": 888, "output_tokens": 300}})
        h = self._run_merge({"2026-07-12": {"input_tokens": 1, "output_tokens": 1}})
        self.assertEqual(h["days"]["2026-07-12"]["antigravity"]["input_tokens"], 888,
                         "Old larger value must be preserved when current is smaller")

    # ── 5. 某日期从当前日志消失后历史保留 ─────────────────────────────────
    def test_05_date_disappears_but_history_retained(self):
        self._run_merge({"2026-05-01": {"input_tokens": 999, "output_tokens": 400}})
        h = self._run_merge({"2026-07-17": {"input_tokens": 50, "output_tokens": 20}})
        self.assertIn("2026-05-01", h["days"])
        self.assertEqual(h["days"]["2026-05-01"]["antigravity"]["input_tokens"], 999)

    # ── 6. dashboard.json 删除后 daily_history 仍存在 ─────────────────────
    def test_06_dashboard_delete_history_survives(self):
        self._run_merge({"2026-07-17": {"input_tokens": 100, "output_tokens": 40}})
        dash = os.path.join(self.tmpdir, "dashboard.json")
        if os.path.exists(dash): os.remove(dash)
        self.assertTrue(os.path.exists(self.hist_path))
        with open(self.hist_path) as f:
            h = json.load(f)
        self.assertIn("2026-07-17", h["days"])

    # ── 7. 损坏时从 .bak 恢复 ─────────────────────────────────────────────
    def test_07_corrupted_file_falls_back_to_bak(self):
        self._run_merge({"2026-07-17": {"input_tokens": 500, "output_tokens": 200}})
        shutil.copy2(self.hist_path, self.bak_path)
        with open(self.hist_path, "w") as f:
            f.write("{CORRUPTED JSON{{")
        result = monitor_backend._safe_load_json(self.hist_path, {"days": {}})
        self.assertIn("days", result)
        self.assertIn("2026-07-17", result["days"])

    # ── 8. 原子写入不会留下半截 JSON ──────────────────────────────────────
    def test_08_atomic_write_no_partial_file(self):
        data = {"version": 2, "updated_at": "2026-07-17 19:00:00",
                "days": {"2026-07-17": {"antigravity": {"input_tokens": 100}}}}
        monitor_backend._atomic_write_json(self.hist_path, data)
        self.assertTrue(os.path.exists(self.hist_path))
        with open(self.hist_path) as f:
            loaded = json.load(f)
        self.assertEqual(loaded["days"]["2026-07-17"]["antigravity"]["input_tokens"], 100)
        self.assertFalse(os.path.exists(self.hist_path + ".tmp"))

    # ── 9. 写入失败时旧文件不被破坏 ────────────────────────────────────────
    def test_09_write_failure_preserves_old(self):
        data_v1 = {"version": 2, "updated_at": "T1",
                   "days": {"2026-07-17": {"antigravity": {"input_tokens": 42}}}}
        monitor_backend._atomic_write_json(self.hist_path, data_v1)
        os.chmod(self.tmpdir, 0o555)
        try:
            monitor_backend._atomic_write_json(self.hist_path, {"version": 2, "days": {}})
        except Exception:
            pass
        finally:
            os.chmod(self.tmpdir, 0o755)
        with open(self.hist_path) as f:
            loaded = json.load(f)
        self.assertEqual(loaded["days"]["2026-07-17"]["antigravity"]["input_tokens"], 42)

    # ── 17. 同日合并取较大值 ──────────────────────────────────────────────
    def test_17_merge_takes_max_same_day(self):
        pre = {"version": 2, "updated_at": "2026-07-16 12:00:00",
               "days": {"2026-07-17": {"antigravity": {
                   "input_tokens": 9999, "output_tokens": 5000,
                   "total_tokens": 14999, "estimated_cost": 1.0}}}}
        with open(self.hist_path, "w") as f:
            json.dump(pre, f)
        h = self._run_merge({"2026-07-17": {"input_tokens": 100, "output_tokens": 40}})
        self.assertEqual(h["days"]["2026-07-17"]["antigravity"]["input_tokens"], 9999)

    # ── 20. 旧 schema 缺少字段时能够兼容 ─────────────────────────────────
    def test_20_missing_fields_compatible(self):
        old = {"version": 1, "updated_at": "2026-01-01 00:00:00",
               "days": {"2026-01-01": {"antigravity": {"input_tokens": 100}}}}
        with open(self.hist_path, "w") as f:
            json.dump(old, f)
        h = self._run_merge({"2026-07-17": {"input_tokens": 50, "output_tokens": 20}})
        self.assertIn("2026-01-01", h["days"])
        self.assertIn("2026-07-17", h["days"])

    # ── Internal helper (v2 schema) ──────────────────────────────────────
    def _run_merge(self, daily_usage: dict) -> dict:
        """Merge step using the new v2 per-source schema."""
        from datetime import datetime
        hist = monitor_backend._safe_load_json(
            self.hist_path, {"version": 2, "updated_at": "", "days": {}})
        if "days" not in hist:
            hist["days"] = {}
        for d, cur in daily_usage.items():
            if d == "未知":
                continue
            prev_day = hist["days"].get(d, {})
            prev_ag  = prev_day.get("antigravity", {})
            cur_inp  = cur.get("input_tokens", 0)
            cur_out  = cur.get("output_tokens", 0)
            new_inp  = int(max(prev_ag.get("input_tokens", 0),  cur_inp))
            new_out  = int(max(prev_ag.get("output_tokens", 0), cur_out))
            new_cost = max(prev_ag.get("estimated_cost", 0.0), _cost(cur_inp, cur_out))
            hist["days"][d] = {"antigravity": {
                "input_tokens":  new_inp,
                "output_tokens": new_out,
                "total_tokens":  new_inp + new_out,
                "estimated_cost": float(new_cost)
            }}
        hist["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        monitor_backend._atomic_write_json(self.hist_path, hist)
        return hist


if __name__ == "__main__":
    unittest.main()
