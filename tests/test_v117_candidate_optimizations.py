"""Regression coverage for the v1.1.8 local optimization candidate.

These tests use temporary files and source contracts for the Swift scheduling
boundary. They never point the scanner at the user's Application Support data.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import monitor_backend


class TestCodexCacheRecoveryAndAtomicity(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cache = os.path.join(self.tmpdir, "codex_scan_cache.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cache_round_trip_uses_atomic_writer_and_backup(self):
        monitor_backend._atomic_write_json(self.cache, {"files": {"a": {"offset": 3}}})
        monitor_backend._atomic_write_json(self.cache, {"files": {"a": {"offset": 7}}})

        self.assertEqual(
            monitor_backend._safe_load_json(self.cache, {})["files"]["a"]["offset"],
            7,
        )
        self.assertEqual(
            json.load(open(self.cache + ".bak"))["files"]["a"]["offset"],
            3,
        )
        self.assertFalse(os.path.exists(self.cache + ".tmp"))

    def test_corrupt_primary_cache_falls_back_to_backup(self):
        with open(self.cache + ".bak", "w", encoding="utf-8") as handle:
            json.dump({"files": {"known": {"offset": 11}}}, handle)
        with open(self.cache, "w", encoding="utf-8") as handle:
            handle.write("{not-json")

        recovered = monitor_backend._safe_load_json(self.cache, {})
        self.assertEqual(recovered["files"]["known"]["offset"], 11)

    def test_both_corrupt_caches_rebuild_as_empty_without_touching_history(self):
        for path in (self.cache, self.cache + ".bak"):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{not-json")

        self.assertEqual(monitor_backend._safe_load_json(self.cache, {}), {})

    def test_failed_cache_write_preserves_primary_and_removes_tmp(self):
        monitor_backend._atomic_write_json(self.cache, {"version": 1})
        with mock.patch.object(monitor_backend.json, "dump", side_effect=OSError("injected")):
            monitor_backend._atomic_write_json(self.cache, {"version": 2})

        self.assertEqual(monitor_backend._safe_load_json(self.cache, {})["version"], 1)
        self.assertFalse(os.path.exists(self.cache + ".tmp"))

    def test_scanner_uses_safe_cache_reader_and_atomic_cache_writer(self):
        source = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
        cache_load = source[source.index("    # Load cache", source.index("def scan_conversations")):
                            source.index("    conversations = {}", source.index("def scan_conversations"))]
        self.assertIn("_safe_load_json(CACHE_FILE, {})", cache_load)
        cache_save = source[source.index("    # Save updated cache"):
                            source.index("    scan_duration_ms", source.index("    # Save updated cache"))]
        self.assertIn("_atomic_write_json(CACHE_FILE, cache)", cache_save)
        self.assertNotIn('open(CACHE_FILE, "w"', cache_save)


class TestSwiftHistoricalModelLoadingBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(
            encoding="utf-8"
        )

    def test_history_extraction_is_scheduled_on_utility_queue(self):
        block_start = self.source.index("func loadLocalCache()")
        block_end = self.source.index("    // MARK: - Timer", block_start)
        block = self.source[block_start:block_end]
        self.assertIn("DispatchQueue.global(qos: .utility).async", block)
        self.assertIn("TokenCacheReader.loadHistoricalModelIds()", block)

    def test_main_queue_only_receives_lightweight_history_result(self):
        block_start = self.source.index("func loadLocalCache()")
        block_end = self.source.index("    // MARK: - Timer", block_start)
        block = self.source[block_start:block_end]
        self.assertIn("self.historicalModelIdsBySource = historicalModelIds", block)
        self.assertIn("self.historyLoadGeneration == generation", block)
        self.assertNotIn(
            "self.historicalModelIdsBySource = TokenCacheReader.loadHistoricalModelIds()",
            block,
        )

    def test_dashboard_and_history_errors_do_not_write_history(self):
        block_start = self.source.index("func loadLocalCache()")
        block_end = self.source.index("    // MARK: - Timer", block_start)
        block = self.source[block_start:block_end]
        self.assertNotIn("dailyHistoryPath", block)
        self.assertNotIn("write(to:", block)

    def test_generation_guard_prevents_stale_refresh_results(self):
        self.assertIn("private var historyLoadGeneration: UInt = 0", self.source)
        self.assertIn("self.historyLoadGeneration &+= 1", self.source)
        self.assertIn("guard let self,", self.source)
        self.assertIn("self.historyLoadGeneration == generation else { return }", self.source)


if __name__ == "__main__":
    unittest.main()
