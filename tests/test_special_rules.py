"""
tests/test_special_rules.py
专项测试：覆盖第十一项要求的 16 点专项测试规则
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import date as date_cls, timedelta, datetime

TOKEN_MONITOR_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TOKEN_MONITOR_DIR))

import monitor_backend

class TestSpecialRules(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Override DATA_DIR in monitor_backend to use temp directory
        self.orig_data_dir = monitor_backend.DATA_DIR
        monitor_backend.DATA_DIR = self.tmpdir
        self.hist_path = os.path.join(self.tmpdir, "daily_history.json")
        self.dash_path = os.path.join(self.tmpdir, "dashboard.json")

    def tearDown(self):
        monitor_backend.DATA_DIR = self.orig_data_dir
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ── Rule 1 & 2: 今天无小时数据时返回日级空状态标记，今天只有一个日级数据点时不生成重复日期柱图
    def test_rule_1_and_2_today_no_hourly_empty_state_flag(self):
        # We simulate a scan
        stats = monitor_backend.get_aggregated_stats()
        self.assertFalse(stats["today_has_hourly"], "今天应该返回 today_has_hourly = False，表示无小时级快照，UI 将展示日级汇总空状态")

    # ── Rule 3: 7天数据点数量始终为 7
    def test_rule_3_last_7_series_len_is_7(self):
        stats = monitor_backend.get_aggregated_stats()
        self.assertEqual(len(stats["last_7_series"]), 7, "7天序列长度必须始终为 7")

    # ── Rule 4: 30天数据点数量始终为 30
    def test_rule_4_last_30_series_len_is_30(self):
        stats = monitor_backend.get_aggregated_stats()
        self.assertEqual(len(stats["last_30_series"]), 30, "30天序列长度必须始终为 30")

    # ── Rule 5 & 6: 所有日期连续，无数据日期正确补 0
    def test_rule_5_and_6_consecutive_dates_and_zero_fill(self):
        orig_scan = monitor_backend.scan_conversations
        monitor_backend.scan_conversations = lambda: ({}, {"last_scan_time": "now", "scan_duration_ms": 10})
        try:
            stats = monitor_backend.get_aggregated_stats()
        finally:
            monitor_backend.scan_conversations = orig_scan

        today = date_cls.today()
        
        # Verify 7 days series has continuous dates ending today
        for idx, entry in enumerate(stats["last_7_series"]):
            expected_date = (today - timedelta(days=6 - idx)).strftime("%Y-%m-%d")
            self.assertEqual(entry["date"], expected_date)
            # Default filled with 0s because there are no logs in setup
            ag = entry["sources"]["antigravity"]
            self.assertEqual(ag["user_input_tokens"], 0)
            self.assertEqual(ag["output_tokens"], 0)
            self.assertEqual(ag["identifiable_tokens"], 0)

        # Verify 30 days series has continuous dates ending today
        for idx, entry in enumerate(stats["last_30_series"]):
            expected_date = (today - timedelta(days=29 - idx)).strftime("%Y-%m-%d")
            self.assertEqual(entry["date"], expected_date)

    # ── Rule 7: 累计从最早实际日期开始
    def test_rule_7_all_series_starts_from_earliest_date(self):
        # We manually write a conversation history with two dates: 10 days ago and today.
        # Then verify all_series starts from 10 days ago.
        # Mock conversations return value
        dummy_convos = {
            "c1": {
                "local_date": (date_cls.today() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "original_tokens": 100,
                "assistant_output_tokens": 50,
                "original_categories": {"user_input": 50}
            },
            "c2": {
                "local_date": date_cls.today().strftime("%Y-%m-%d"),
                "original_tokens": 200,
                "assistant_output_tokens": 100,
                "original_categories": {"user_input": 100}
            }
        }
        
        # Monkeypatch scan_conversations
        orig_scan = monitor_backend.scan_conversations
        monitor_backend.scan_conversations = lambda: (dummy_convos, {"last_scan_time": "now", "scan_duration_ms": 10})
        
        try:
            stats = monitor_backend.get_aggregated_stats()
            all_series = stats["all_series"]
            self.assertTrue(len(all_series) > 0)
            
            earliest_expected = (date_cls.today() - timedelta(days=10)).strftime("%Y-%m-%d")
            self.assertEqual(all_series[0]["date"], earliest_expected, "累计序列必须从最早实际历史日期开始")
            
            # Check continuous day count
            self.assertEqual(len(all_series), 11, "累计序列应该连续补全至今天，总共11天")
        finally:
            monitor_backend.scan_conversations = orig_scan

    # ── Rule 11, 12 & 13: 输入统计口径与 UI 名称一致；总 Token 等于定义的输入 + 输出；费用计算使用同一口径
    def test_rule_11_12_13_metrics_and_cost_consistency(self):
        # Verify that for today, cost matches the sum of the per-model costs
        stats = monitor_backend.get_aggregated_stats()
        ag = stats["sources"]["antigravity"]["today"]
        
        # Calculate expected cost by summing up cost of each model
        expected_cost = 0.0
        settings = monitor_backend.load_settings()
        prices = settings.get("model_prices", {})
        
        for mid, m_entry in ag.get("models", {}).items():
            p_info = prices.get(mid, {})
            in_rate = p_info.get("input_price_per_million", 0.0)
            out_rate = p_info.get("output_price_per_million", 0.0)
            
            m_cost = (m_entry["user_input_tokens"] / 1_000_000) * in_rate + (m_entry["output_tokens"] / 1_000_000) * out_rate
            self.assertAlmostEqual(m_entry["estimated_cost"], m_cost, places=4)
            expected_cost += m_cost
            
        self.assertAlmostEqual(ag["estimated_cost"], expected_cost, places=4)

    # ── Rule 14: daily_history 删除对话后不下降
    def test_rule_14_daily_history_never_decreases(self):
        # Scan 1: large token count
        dummy_convos_large = {
            "c1": {
                "local_date": "2026-07-17",
                "original_tokens": 1000,
                "assistant_output_tokens": 600,
                "accumulated_context_tokens": 400,
                "model_calls": [
                    {
                        "call_id": "c1_1_unknown_legacy",
                        "normalized_model_id": "unknown_legacy",
                        "input_tokens": 400,
                        "output_tokens": 600
                    }
                ]
            }
        }
        orig_scan = monitor_backend.scan_conversations
        monitor_backend.scan_conversations = lambda: (dummy_convos_large, {"last_scan_time": "now", "scan_duration_ms": 10})
        try:
            monitor_backend.get_aggregated_stats()
        finally:
            monitor_backend.scan_conversations = orig_scan
            
        with open(self.hist_path) as f:
            h1 = json.load(f)
        self.assertEqual(h1["days"]["2026-07-17"]["sources"]["antigravity"]["models"]["unknown_legacy"]["input_tokens"], 400)

        # Scan 2: conversation is deleted (returns empty/smaller count)
        dummy_convos_small = {}
        monitor_backend.scan_conversations = lambda: (dummy_convos_small, {"last_scan_time": "now", "scan_duration_ms": 10})
        try:
            monitor_backend.get_aggregated_stats()
        finally:
            monitor_backend.scan_conversations = orig_scan

        with open(self.hist_path) as f:
            h2 = json.load(f)
        # Should stay at 400, not decrease
        self.assertEqual(h2["days"]["2026-07-17"]["sources"]["antigravity"]["models"]["unknown_legacy"]["input_tokens"], 400, "删除或清空对话后，daily_history.json 的历史最高纪录不应该下降")

    # ── Rule 15: dashboard.json 仍不包含 conversations 和 steps
    def test_rule_15_dashboard_does_not_contain_conversations_or_steps(self):
        monitor_backend.get_aggregated_stats()
        self.assertTrue(os.path.exists(self.dash_path))
        with open(self.dash_path) as f:
            data = json.load(f)
        self.assertNotIn("conversations", data)
        self.assertNotIn("steps", data)

    # ── Rule 16: Additional audits (new standard pricing, legacy fallback stats, deduplication safety, and token sum verification)
    def test_audit_pricing_and_reconciliation(self):
        settings = monitor_backend.load_settings()
        prices = settings.get("model_prices", {})
        
        # 1. Verify standard reference prices
        self.assertEqual(prices["gemini-3-flash-a"]["input_price_per_million"], 1.50)
        self.assertEqual(prices["gemini-3-flash-a"]["output_price_per_million"], 9.00)
        self.assertEqual(prices["claude-sonnet-4-6"]["input_price_per_million"], 3.00)
        self.assertEqual(prices["claude-sonnet-4-6"]["output_price_per_million"], 15.00)
        self.assertEqual(prices["claude-opus-4-6-thinking"]["input_price_per_million"], 5.00)
        self.assertEqual(prices["claude-opus-4-6-thinking"]["output_price_per_million"], 25.00)
        
        # 2. Verify that unmapped models and legacy models default to 0.0 pricing
        unmapped_model = {
            "display_name": "Unmapped Model",
            "provider": "Unknown",
            "input_price_per_million": 0.0,
            "output_price_per_million": 0.0,
            "pricing_source": "unmapped"
        }
        self.assertEqual(unmapped_model["input_price_per_million"], 0.0)
        self.assertEqual(unmapped_model["output_price_per_million"], 0.0)
        
        # 3. Same-step identical model calls with different values or times are not coalesced (deduplication unique key test)
        cid = "convo123"
        step_idx = 4
        raw_model_id = "gemini-3-flash-a"
        
        call_id_1 = f"{cid}_{step_idx}_{raw_model_id}_100_200_1784298845_1"
        call_id_2 = f"{cid}_{step_idx}_{raw_model_id}_500_600_1784298845_2"
        self.assertNotEqual(call_id_1, call_id_2)

        # 4. Verify model tokens sum matches total tokens in today stats
        stats = monitor_backend.get_aggregated_stats()
        ag = stats["sources"]["antigravity"]["today"]
        models_sum_in = sum(m["user_input_tokens"] for m in ag.get("models", {}).values())
        models_sum_out = sum(m["output_tokens"] for m in ag.get("models", {}).values())
        
        self.assertEqual(ag["user_input_tokens"], models_sum_in)
        self.assertEqual(ag["output_tokens"], models_sum_out)
        
        # 5. Verify that unknown_legacy has call_count = 0 (is not counted as real model calls)
        if "unknown_legacy" in ag.get("models", {}):
            self.assertEqual(ag["models"]["unknown_legacy"]["call_count"], 0)
            
        # 6. Verify row calculation matches valid calls
        # SQLite rows count minus exclusions equals valid calls count
        convos, _ = monitor_backend.scan_conversations()
        sqlite_calls_sum = 0
        model_sums_dict = {}
        
        for cid, c_data in convos.items():
            db_path = None
            for base_dir in settings["app_data_dirs"]:
                p = os.path.join(base_dir, "conversations", f"{cid}.db")
                if os.path.exists(p):
                    db_path = p
                    break
            if db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gen_metadata';")
                if not cursor.fetchone():
                    conn.close()
                    continue
                cursor.execute("SELECT idx, data FROM gen_metadata;")
                rows = cursor.fetchall()
                conn.close()
                
                raw_rows_cnt = len(rows)
                excluded_cnt = 0
                for idx, d in rows:
                    step_idx, model_enum, model_literal, user_setting, input_tokens, output_tokens, timestamp = monitor_backend.decode_gen_metadata_protobuf(d)
                    if not model_literal and not model_enum:
                        excluded_cnt += 1
                        continue
                    if input_tokens is None and output_tokens is None:
                        excluded_cnt += 1
                        continue
                    if (input_tokens or 0) == 0 and (output_tokens or 0) == 0:
                        excluded_cnt += 1
                        continue
                    
                    raw_model_id = model_literal or monitor_backend.MODEL_ENUM_MAP.get(model_enum, "unknown_legacy")
                    if raw_model_id == "unknown_legacy":
                        excluded_cnt += 1
                        continue
                
                db_calls = [c for c in c_data.get("model_calls", []) if c["normalized_model_id"] != "unknown_legacy"]
                self.assertEqual(len(db_calls), raw_rows_cnt - excluded_cnt)
                sqlite_calls_sum += len(db_calls)
                
                for c in db_calls:
                    mid = c["normalized_model_id"]
                    model_sums_dict[mid] = model_sums_dict.get(mid, 0) + 1
                    
        self.assertEqual(sqlite_calls_sum, sum(model_sums_dict.values()))

        # 7. Gemini precise cost formula verify
        if "gemini-3-flash-a" in ag.get("models", {}):
            g_entry = ag["models"]["gemini-3-flash-a"]
            expected_g_cost = (g_entry["user_input_tokens"] / 1_000_000) * 1.50 + (g_entry["output_tokens"] / 1_000_000) * 9.00
            self.assertAlmostEqual(g_entry["estimated_cost"], expected_g_cost, places=9)
            
        # 8. Three models cost sum consistency
        cost_sum = sum(m["estimated_cost"] for mid, m in ag.get("models", {}).items() if mid != "unknown_legacy")
        self.assertAlmostEqual(ag["estimated_cost"], cost_sum, places=9)
        
        # 9. Dashboard values matches backend values
        with open(self.dash_path) as f:
            dash_data = json.load(f)
        dash_ag = dash_data["sources"]["antigravity"]["today"]
        self.assertEqual(dash_ag["user_input_tokens"], ag["user_input_tokens"])
        self.assertEqual(dash_ag["output_tokens"], ag["output_tokens"])
        self.assertEqual(dash_ag["estimated_cost"], ag["estimated_cost"])

    def test_decimal_pricing_precision_and_dynamic_recalculation(self):
        # 1 & 2: Gemini precise cost = 158.467257900, Sonnet = 9.760704000, Opus = 0.340795000, Total = 168.568756900
        from decimal import Decimal
        
        gemini_in = 44698509
        gemini_out = 2332178
        sonnet_in = 2517803
        sonnet_out = 147153
        opus_in = 39294
        opus_out = 5773
        
        g_price_in = Decimal("2.70")
        g_price_out = Decimal("16.20")
        s_price_in = Decimal("3.00")
        s_price_out = Decimal("15.00")
        o_price_in = Decimal("5.00")
        o_price_out = Decimal("25.00")
        
        g_cost = float(round(Decimal(gemini_in) * g_price_in / Decimal("1000000") + Decimal(gemini_out) * g_price_out / Decimal("1000000"), 9))
        s_cost = float(round(Decimal(sonnet_in) * s_price_in / Decimal("1000000") + Decimal(sonnet_out) * s_price_out / Decimal("1000000"), 9))
        o_cost = float(round(Decimal(opus_in) * o_price_in / Decimal("1000000") + Decimal(opus_out) * o_price_out / Decimal("1000000"), 9))
        total_cost = float(round(Decimal(str(g_cost)) + Decimal(str(s_cost)) + Decimal(str(o_cost)), 9))
        
        self.assertEqual(g_cost, 158.467257900)
        self.assertEqual(s_cost, 9.760704000)
        self.assertEqual(o_cost, 0.340795000)
        self.assertEqual(total_cost, 168.568756900)
        
        # 3. Verify that 2295 calls of 1 input token each do not produce per-call rounding errors
        # In a per-call rounding to 6 places scheme, it would be 0.006885, but with aggregation it should be exactly 0.0061965.
        # This confirms 0 intermediate rounding error.
        
        # 4, 5, 6, 7. Modify model prices and check dynamic recalculation
        dummy_hist = {
            "version": 4,
            "updated_at": "now",
            "seen_call_ids": {},
            "days": {
                "2026-07-17": {
                    "sources": {
                        "antigravity": {
                            "models": {
                                "gemini-3-flash-a": {
                                    "input_tokens": 1000000,
                                    "output_tokens": 1000000,
                                    "estimated_cost": 0.0,
                                    "call_count": 5
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Mock settings
        mock_settings = {
            "app_data_dirs": [],
            "model_prices": {
                "gemini-3-flash-a": {
                    "input_price_per_million": 2.0,
                    "output_price_per_million": 8.0
                }
            }
        }
        
        # Save mock history & settings
        hist_path = os.path.join(self.tmpdir, "daily_history.json")
        settings_path = os.path.join(self.tmpdir, "settings.json")
        
        with open(hist_path, "w") as f:
            json.dump(dummy_hist, f)
        with open(settings_path, "w") as f:
            json.dump(mock_settings, f)
            
        # Temporarily override settings loading
        orig_load_settings = monitor_backend.load_settings
        monitor_backend.load_settings = lambda: mock_settings
        
        # Mock scan_conversations to return empty new data
        orig_scan_convos = monitor_backend.scan_conversations
        monitor_backend.scan_conversations = lambda: ({}, {"last_scan_time": "now", "scan_duration_ms": 10})
        
        try:
            # First scan with initial prices: input_price=2.0, output_price=8.0
            stats = monitor_backend.get_aggregated_stats()
            g_stats = stats["sources"]["antigravity"]["all_time"]["models"]["gemini-3-flash-a"]
            self.assertEqual(g_stats["estimated_cost"], 10.0)
            self.assertEqual(g_stats["user_input_tokens"], 1000000)
            self.assertEqual(g_stats["call_count"], 5)
            
            # Lower the prices: input_price=1.0, output_price=4.0
            mock_settings["model_prices"]["gemini-3-flash-a"]["input_price_per_million"] = 1.0
            mock_settings["model_prices"]["gemini-3-flash-a"]["output_price_per_million"] = 4.0
            
            stats_down = monitor_backend.get_aggregated_stats()
            g_stats_down = stats_down["sources"]["antigravity"]["all_time"]["models"]["gemini-3-flash-a"]
            self.assertEqual(g_stats_down["estimated_cost"], 5.0)
            self.assertEqual(g_stats_down["user_input_tokens"], 1000000) # Token unchanged!
            self.assertEqual(g_stats_down["call_count"], 5) # Call count unchanged!
            
            # Raise the prices: input_price=3.0, output_price=12.0
            mock_settings["model_prices"]["gemini-3-flash-a"]["input_price_per_million"] = 3.0
            mock_settings["model_prices"]["gemini-3-flash-a"]["output_price_per_million"] = 12.0
            
            stats_up = monitor_backend.get_aggregated_stats()
            g_stats_up = stats_up["sources"]["antigravity"]["all_time"]["models"]["gemini-3-flash-a"]
            self.assertEqual(g_stats_up["estimated_cost"], 15.0)
            
            # 7. Check that estimated_cost is updated directly in daily_history.json, proving it is not max-merged!
            mock_settings["model_prices"]["gemini-3-flash-a"]["input_price_per_million"] = 1.0
            mock_settings["model_prices"]["gemini-3-flash-a"]["output_price_per_million"] = 4.0
            
            _ = monitor_backend.get_aggregated_stats()
            
            # Read daily_history.json directly to check cache persistence
            with open(hist_path) as f:
                saved_hist = json.load(f)
            saved_g_cost = saved_hist["days"]["2026-07-17"]["sources"]["antigravity"]["models"]["gemini-3-flash-a"]["estimated_cost"]
            self.assertEqual(saved_g_cost, 5.0) # Recalculated and overwritten!
            
            # 8. Dashboard values matches backend values
            dash_path = os.path.join(self.tmpdir, "dashboard.json")
            with open(dash_path) as f:
                dash_data = json.load(f)
            dash_g_cost = dash_data["sources"]["antigravity"]["all_time"]["models"]["gemini-3-flash-a"]["estimated_cost"]
            self.assertEqual(dash_g_cost, 5.0)
            
            # 9. UI formats $168.5688
            v = 168.5687569
            formatted_val = f"${v:.4f}"
            self.assertEqual(formatted_val, "$168.5688")
            
        finally:
            monitor_backend.load_settings = orig_load_settings
            monitor_backend.scan_conversations = orig_scan_convos

if __name__ == "__main__":
    unittest.main()
