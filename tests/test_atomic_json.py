"""
tests/test_atomic_json.py
专项测试：_atomic_write_json / _safe_load_json 原子写入与备份恢复
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


class TestAtomicJSON(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path   = os.path.join(self.tmpdir, "test_atomic.json")
        self.bak    = self.path + ".bak"
        self.tmp    = self.path + ".tmp"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_atomic_creates_file(self):
        data = {"key": "value", "num": 42}
        monitor_backend._atomic_write_json(self.path, data)
        self.assertTrue(os.path.exists(self.path))
        with open(self.path) as f:
            loaded = json.load(f)
        self.assertEqual(loaded["num"], 42)

    def test_atomic_no_tmp_file_remains(self):
        monitor_backend._atomic_write_json(self.path, {"a": 1})
        self.assertFalse(os.path.exists(self.tmp), ".tmp file must be cleaned up after atomic write")

    def test_atomic_creates_bak_on_overwrite(self):
        monitor_backend._atomic_write_json(self.path, {"version": 1})
        monitor_backend._atomic_write_json(self.path, {"version": 2})
        self.assertTrue(os.path.exists(self.bak), ".bak should exist after overwrite")
        with open(self.bak) as f:
            bak_data = json.load(f)
        self.assertEqual(bak_data["version"], 1)

    def test_safe_load_reads_main_file(self):
        data = {"days": {"2026-07-17": {"user_input": 999}}}
        with open(self.path, "w") as f:
            json.dump(data, f)
        result = monitor_backend._safe_load_json(self.path, {})
        self.assertEqual(result["days"]["2026-07-17"]["user_input"], 999)

    def test_safe_load_falls_back_to_bak(self):
        bak_data = {"days": {"2026-06-01": {"user_input": 777}}}
        with open(self.bak, "w") as f:
            json.dump(bak_data, f)
        with open(self.path, "w") as f:
            f.write("INVALID JSON{{{{")
        result = monitor_backend._safe_load_json(self.path, {"days": {}})
        self.assertIn("2026-06-01", result.get("days", {}))

    def test_safe_load_returns_default_when_both_missing(self):
        result = monitor_backend._safe_load_json(self.path, {"default": True})
        self.assertTrue(result.get("default"))

    def test_safe_load_returns_default_when_both_corrupted(self):
        for p in [self.path, self.bak]:
            with open(p, "w") as f:
                f.write("{BAD}")
        result = monitor_backend._safe_load_json(self.path, {"fallback": 99})
        self.assertEqual(result.get("fallback"), 99)

    def test_safe_load_returns_default_when_file_absent_and_no_bak(self):
        result = monitor_backend._safe_load_json("/tmp/nonexistent_xyz.json", {"x": 1})
        self.assertEqual(result.get("x"), 1)

    def test_written_json_is_valid_utf8(self):
        data = {"msg": "你好世界 🛸"}
        monitor_backend._atomic_write_json(self.path, data)
        with open(self.path, encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["msg"], "你好世界 🛸")

    def test_large_write_integrity(self):
        """Write a large dict and verify it's fully readable."""
        data = {"days": {f"2026-{m:02d}-{d:02d}": {"user_input": m * d}
                         for m in range(1, 13) for d in range(1, 29)}}
        monitor_backend._atomic_write_json(self.path, data)
        loaded = monitor_backend._safe_load_json(self.path, {})
        self.assertEqual(len(loaded["days"]), 12 * 28)


if __name__ == "__main__":
    unittest.main()
