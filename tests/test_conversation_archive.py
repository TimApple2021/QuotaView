"""
tests/test_conversation_archive.py
专项测试：conversation_history.json 对话级归档账本 + 删除归档还原模拟
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOKEN_MONITOR_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TOKEN_MONITOR_DIR))

import monitor_backend


# ── Minimal fake convo_list item ────────────────────────────────────────────

def _fake_convo(cid="conv_A", title="测试对话 A", steps=5,
                raw=1000, accum=10000, output=500, cost=0.05,
                last_active="2026-07-17T10:00:00"):
    return {
        "id": cid, "title": title,
        "created_at": "2026-07-17T09:00:00",
        "last_active": last_active,
        "steps_count": steps,
        "original_tokens": raw,
        "accumulated_context_tokens": accum,
        "assistant_output_tokens": output,
        "cost": cost,
        "original_categories": {},
        "steps": []
    }


def _run_conv_history_merge(conv_history_path: str, convo_list: list) -> dict:
    """Replicate monitor_backend's conversation_history update logic."""
    from datetime import datetime
    conv_history = monitor_backend._safe_load_json(
        conv_history_path, {"version": 1, "updated_at": "", "conversations": {}})
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
            "estimated_cost":      max(prev.get("estimated_cost", 0.0), item.get("cost", 0.0)),
            "status":              "active",
            "source_path":         cid,
            "snapshot_only":       False
        }

    for cid, entry in conv_history["conversations"].items():
        if cid not in active_ids and entry.get("status") == "active":
            conv_history["conversations"][cid]["status"] = "archived"
            conv_history["conversations"][cid]["snapshot_only"] = True

    conv_history["updated_at"] = now_str
    monitor_backend._atomic_write_json(conv_history_path, conv_history)
    return conv_history


class TestConversationArchive(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.conv_path = os.path.join(self.tmpdir, "conversation_history.json")
        self.bak_path  = self.conv_path + ".bak"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── 10. conversation_history 首次创建 ─────────────────────────────────
    def test_10_first_creation(self):
        self.assertFalse(os.path.exists(self.conv_path))
        h = _run_conv_history_merge(self.conv_path, [_fake_convo()])
        self.assertTrue(os.path.exists(self.conv_path))
        self.assertIn("conv_A", h["conversations"])

    # ── 11. 同一对话重复扫描不会重复创建 ────────────────────────────────────
    def test_11_no_duplicate_on_rescan(self):
        _run_conv_history_merge(self.conv_path, [_fake_convo()])
        h = _run_conv_history_merge(self.conv_path, [_fake_convo()])
        self.assertEqual(len(h["conversations"]), 1)

    # ── 12. 当前对话消失后 status = archived ─────────────────────────────
    def test_12_disappears_becomes_archived(self):
        _run_conv_history_merge(self.conv_path, [_fake_convo("conv_A"), _fake_convo("conv_B")])
        # Next scan conv_A is gone
        h = _run_conv_history_merge(self.conv_path, [_fake_convo("conv_B")])
        self.assertEqual(h["conversations"]["conv_A"]["status"], "archived")
        self.assertEqual(h["conversations"]["conv_B"]["status"], "active")

    # ── 13. 归档对话重新出现后恢复 active ─────────────────────────────────
    def test_13_archived_restored_to_active(self):
        _run_conv_history_merge(self.conv_path, [_fake_convo("conv_A")])
        _run_conv_history_merge(self.conv_path, [])          # conv_A disappears → archived
        h = _run_conv_history_merge(self.conv_path, [_fake_convo("conv_A")])  # comes back
        self.assertEqual(h["conversations"]["conv_A"]["status"], "active")
        self.assertFalse(h["conversations"]["conv_A"]["snapshot_only"])

    # ── 14. 历史摘要字段使用 max 合并 ────────────────────────────────────
    def test_14_max_merge_on_rescan(self):
        _run_conv_history_merge(self.conv_path, [_fake_convo("conv_A", raw=9000)])
        h = _run_conv_history_merge(self.conv_path, [_fake_convo("conv_A", raw=100)])
        self.assertEqual(h["conversations"]["conv_A"]["raw_tokens"], 9000,
                         "raw_tokens should keep historical max when current is smaller")

    # ── 15. 不保存正文、Prompt、步骤内容 ─────────────────────────────────
    def test_15_no_text_content_saved(self):
        # Even if steps list has content in the convo, the merge should not persist it
        convo = _fake_convo()
        convo["steps"] = [{"type": "USER_INPUT", "content": "SECRET PROMPT TEXT", "tokens": 999}]
        _run_conv_history_merge(self.conv_path, [convo])
        with open(self.conv_path) as f:
            raw_text = f.read()
        self.assertNotIn("SECRET PROMPT TEXT", raw_text,
                         "Steps content/Prompt must never appear in conversation_history.json")

    # ── 16. 损坏时从 .bak 恢复 ──────────────────────────────────────────
    def test_16_corrupted_recovers_from_bak(self):
        _run_conv_history_merge(self.conv_path, [_fake_convo("conv_A", raw=777)])
        shutil.copy2(self.conv_path, self.bak_path)
        with open(self.conv_path, "w") as f:
            f.write("{{NOT JSON}}")
        result = monitor_backend._safe_load_json(self.conv_path, {"conversations": {}})
        self.assertIn("conv_A", result.get("conversations", {}))

    # ── 18. 归档对话字段可被正确解码 ─────────────────────────────────────
    def test_18_archived_entry_decodable(self):
        _run_conv_history_merge(self.conv_path, [_fake_convo("conv_Z")])
        _run_conv_history_merge(self.conv_path, [])  # archive it
        with open(self.conv_path) as f:
            data = json.load(f)
        entry = data["conversations"]["conv_Z"]
        required_keys = ["id", "title", "status", "raw_tokens", "accumulated_context",
                         "output_tokens", "estimated_cost", "snapshot_only"]
        for k in required_keys:
            self.assertIn(k, entry, f"Missing key: {k}")
        self.assertEqual(entry["status"], "archived")
        self.assertTrue(entry["snapshot_only"])

    # ── 19. 空历史文件不导致崩溃 ────────────────────────────────────────
    def test_19_empty_history_file_safe(self):
        with open(self.conv_path, "w") as f:
            f.write("{}")
        result = monitor_backend._safe_load_json(self.conv_path, {"conversations": {}})
        self.assertIsInstance(result, dict)
        # merge with empty history should work without exception
        try:
            _run_conv_history_merge(self.conv_path, [_fake_convo()])
        except Exception as e:
            self.fail(f"Empty history caused exception: {e}")


class TestDeleteArchiveSimulation(unittest.TestCase):
    """
    End-to-end simulation: create test conversation, scan, delete, re-scan.
    Uses only tmpdir — never touches real Antigravity directories.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.conv_path = os.path.join(self.tmpdir, "conversation_history.json")
        self.hist_path = os.path.join(self.tmpdir, "daily_history.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _merge_daily(self, daily_usage):
        """Minimal daily_history merge."""
        from datetime import datetime
        hist = monitor_backend._safe_load_json(
            self.hist_path, {"version": 1, "updated_at": "", "days": {}})
        if "days" not in hist:
            hist["days"] = {}
        for date, cur in daily_usage.items():
            if date == "未知":
                continue
            prev = hist["days"].get(date, {})
            hist["days"][date] = {
                "user_input":          int(max(prev.get("user_input", 0),          cur.get("user_input", 0))),
                "assistant_output":    int(max(prev.get("assistant_output", 0),    cur.get("assistant_output", 0))),
                "tool_returns":        int(max(prev.get("tool_returns", 0),        cur.get("tool_returns", 0))),
                "raw_tokens":          int(max(prev.get("raw_tokens", 0),          cur.get("original", 0))),
                "accumulated_context": int(max(prev.get("accumulated_context", 0), cur.get("accumulated_context", 0))),
                "estimated_cost":      float(max(prev.get("estimated_cost", 0.0),  cur.get("cost", 0.0))),
            }
        hist["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        monitor_backend._atomic_write_json(self.hist_path, hist)
        return hist

    def test_full_lifecycle_delete_restore(self):
        """
        Step 1-11: Create A → scan → enlarge → rescan → delete → rescan → confirm archived →
                   restore → rescan → confirm active.
        """
        convo_A = _fake_convo("conv_A", raw=1000, accum=10000)
        day_usage = {"2026-07-17": {"original": 1000, "accumulated_context": 10000,
                                     "assistant_output": 400, "user_input": 200,
                                     "tool_returns": 100, "cost": 0.08}}

        # === Step 1-3: Initial scan ===
        _run_conv_history_merge(self.conv_path, [convo_A])
        self._merge_daily(day_usage)

        with open(self.conv_path) as f:
            h = json.load(f)
        self.assertIn("conv_A", h["conversations"])
        self.assertEqual(h["conversations"]["conv_A"]["status"], "active")
        with open(self.hist_path) as f:
            dh = json.load(f)
        self.assertIn("2026-07-17", dh["days"])

        # === Step 4-5: Token count grows ===
        bigger_A = _fake_convo("conv_A", raw=5000, accum=50000)
        bigger_day = {"2026-07-17": {"original": 5000, "accumulated_context": 50000,
                                      "assistant_output": 2000, "user_input": 1000,
                                      "tool_returns": 500, "cost": 0.40}}
        _run_conv_history_merge(self.conv_path, [bigger_A])
        self._merge_daily(bigger_day)
        with open(self.conv_path) as f:
            h = json.load(f)
        self.assertEqual(h["conversations"]["conv_A"]["raw_tokens"], 5000)

        # === Step 6-8: Delete conv_A, rescan without it ===
        _run_conv_history_merge(self.conv_path, [])   # conv_A absent
        self._merge_daily({})                          # no daily_usage today
        with open(self.conv_path) as f:
            h = json.load(f)
        self.assertIn("conv_A", h["conversations"], "conv_A must still exist after deletion")
        self.assertEqual(h["conversations"]["conv_A"]["status"], "archived")
        # daily_history must NOT drop
        with open(self.hist_path) as f:
            dh = json.load(f)
        self.assertEqual(dh["days"]["2026-07-17"]["raw_tokens"], 5000,
                         "Daily history must not drop when conversation is deleted")

        # === Step 9-11: Restore conv_A ===
        _run_conv_history_merge(self.conv_path, [bigger_A])
        with open(self.conv_path) as f:
            h = json.load(f)
        self.assertEqual(h["conversations"]["conv_A"]["status"], "active")
        self.assertFalse(h["conversations"]["conv_A"]["snapshot_only"])


if __name__ == "__main__":
    unittest.main()
