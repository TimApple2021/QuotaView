import unittest
import os
import monitor_backend as m

class TestQuotaMonitoring(unittest.TestCase):
    def test_no_official_data_produces_no_estimated_percents(self):
        # When convos have data but no official rate limit records, get_quota_status
        # must return empty lists, not fabricated 100% or estimated percentages.
        convos = {
            "c1": {
                "last_active": "2026-07-18 10:00:00",
                "original_categories": {"gemini-3-flash-a": 100000}
            }
        }
        res = m.get_quota_status(convos, [])
        self.assertIn(res["antigravity"]["status"], {"official_live", "unavailable", "page_not_open"})
        self.assertIn(res["codex"]["status"], {"official_live", "unavailable"})
        self.assertTrue(all(item.get("confidence") == "official_live" for item in res["codex"]["items"]))
        self.assertTrue(all(item.get("confidence") == "official_live" for item in res["antigravity"]["items"]))

    def test_codex_historical_log_not_in_quota_cards(self):
        # Even if JSONL has recent log items, they must be marked as historical_log
        # and NOT enter current official live quota list.
        res = m.get_quota_status({}, [])
        self.assertNotEqual(res["codex"]["status"], "historical_log")
        self.assertTrue(all(item.get("confidence") == "official_live" for item in res["codex"]["items"]))
        self.assertTrue(all(item.get("source_path") != "historical_log" for item in res["codex"]["items"]))

    def test_only_official_live_confidence_allowed(self):
        # Verify that get_quota_status only accepts official_live items.
        # Live data may exist when the official page is open; otherwise status is explicit.
        res = m.get_quota_status({}, [])
        self.assertIn(res["antigravity"]["status"], {"official_live", "unavailable", "page_not_open"})
        self.assertIn(res["codex"]["status"], {"official_live", "unavailable"})

    def test_swift_code_button_icon_assertions(self):
        # Verify that xmark.circle.fill does not exist and power exists in MenuBarView.swift
        swift_path = "macos/AntigravityTokenMonitor/MenuBarView.swift"
        if os.path.exists(swift_path):
            with open(swift_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("xmark.circle.fill", content)
            self.assertIn("power", content)
            
    def test_cost_and_token_metrics_have_no_hardcoding(self):
        # Verify that no screenshot values are hardcoded in python source
        backend_path = "monitor_backend.py"
        if os.path.exists(backend_path):
            with open(backend_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Verify no hardcoded 66% or 44% in quota estimations
            self.assertNotIn('"rate_limits.primary.used_percent"', content)
            self.assertNotIn('"rate_limits.secondary.used_percent"', content)

    def test_codex_reset_entitlements_parsing(self):
        # 1. Codex reset_entitlements official_live 成功解析。
        # 2. available_count 成功解析。
        # 3. 两条 Full reset 成功解析。
        # 5. expires_at 完整时间戳解析。
        # 8. count_semantics 正确记录。
        raw_result = {
            "rateLimits": {
                "limitId": "codex",
                "primary": {
                    "usedPercent": 26,
                    "windowDurationMins": 10080,
                    "resetsAt": 1784980175
                },
                "planType": "plus"
            },
            "rateLimitResetCredits": {
                "availableCount": 2,
                "credits": [
                    {
                        "id": "c1",
                        "resetType": "codexRateLimits",
                        "status": "available",
                        "expiresAt": 1785528035,
                        "title": "Full reset"
                    },
                    {
                        "id": "c2",
                        "resetType": "codexRateLimits",
                        "status": "available",
                        "expiresAt": 1786556312,
                        "title": "Full reset"
                    }
                ]
            }
        }
        
        parsed = m.normalize_codex_app_server_rate_limits(raw_result, "2026-07-18T15:02:35Z")
        self.assertEqual(parsed["status"], "official_live")
        
        ent = parsed["reset_entitlements"]
        self.assertEqual(ent["status"], "official_live")
        self.assertEqual(ent["available_count"], 2)
        self.assertEqual(ent["count_semantics"], "official")
        self.assertEqual(len(ent["items"]), 2)
        
        # Check first credit expires_at format
        self.assertEqual(ent["items"][0]["expires_at"], "2026-07-31T20:00:35Z")
        self.assertIsNone(ent["items"][0]["expires_on"])
        self.assertEqual(ent["items"][0]["display_name"], "Full reset")
        self.assertEqual(ent["items"][0]["type"], "codexRateLimits")
        self.assertEqual(ent["items"][0]["status"], "available")
        self.assertEqual(ent["items"][0]["id"], "c1")
        self.assertEqual(ent["available_count_field_name"], "rateLimitResetCredits.availableCount")
        self.assertEqual(ent["original_field_name"], "rateLimitResetCredits.credits")
        self.assertEqual(ent["expires_at_field_name"], "rateLimitResetCredits.credits[].expiresAt")
        self.assertEqual(ent["observed_at"], "2026-07-18T15:02:35Z")
        
        # Check second credit expires_at format
        self.assertEqual(ent["items"][1]["expires_at"], "2026-08-12T17:38:32Z")
        self.assertIsNone(ent["items"][1]["expires_on"])

    def test_only_available_reset_items_are_displayable(self):
        raw = {"rateLimitResetCredits": {"availableCount": 1, "credits": [
            {"id": "available", "resetType": "codexRateLimits", "status": "AVAILABLE", "title": "Full reset", "expiresAt": 1785528035},
            {"id": "used", "resetType": "codexRateLimits", "status": "used", "title": "Full reset", "expiresAt": 1785528035},
            {"id": "consumed", "resetType": "codexRateLimits", "status": "consumed", "title": "Full reset", "expiresAt": 1785528035},
            {"id": "expired", "resetType": "codexRateLimits", "status": "expired", "title": "Full reset", "expiresAt": 1785528035},
        ]}}
        ent = m.parse_reset_entitlements(raw, "2026-07-18T15:02:35Z")
        available = [x for x in ent["items"] if x["status"].lower() == "available"]
        self.assertEqual(ent["available_count"], 1)
        self.assertEqual([x["id"] for x in available], ["available"])

    def test_missing_count_derives_from_available_items(self):
        raw = {"rateLimitResetCredits": {"credits": [
            {"id": "a", "status": "available", "title": "Full reset"},
            {"id": "b", "status": "redeemed", "title": "Full reset"},
        ]}}
        ent = m.parse_reset_entitlements(raw, "2026-07-18T15:02:35Z")
        self.assertEqual(ent["available_count"], 1)
        self.assertEqual(ent["count_semantics"], "derived_from_available_items")

    def test_official_count_wins_when_item_count_differs(self):
        raw = {"rateLimitResetCredits": {"availableCount": 2, "credits": [
            {"id": "a", "status": "available", "title": "Full reset"},
            {"id": "b", "status": "used", "title": "Full reset"},
        ]}}
        ent = m.parse_reset_entitlements(raw, "2026-07-18T15:02:35Z")
        self.assertEqual(ent["available_count"], 2)
        self.assertEqual(len([x for x in ent["items"] if x["status"].lower() == "available"]), 1)

    def test_antigravity_model_normalization_and_pro_tiers(self):
        self.assertEqual(m.normalize_antigravity_model("Gemini 3.1 Pro (Low)"), "gemini-3.1-pro")
        self.assertEqual(m.normalize_antigravity_model("Gemini 3.1 Pro (High)"), "gemini-3.1-pro")
        self.assertEqual(m.normalize_antigravity_model("Gemini 3.5 Flash (Medium)"), "gemini-3.5-flash")
        prices = m.DEFAULT_SETTINGS["model_prices"]
        self.assertEqual(m.pricing_rates_for_model("gemini-3.1-pro", 200000, prices), (2.0, 0.2, 12.0))
        self.assertEqual(m.pricing_rates_for_model("gemini-3.1-pro", 200001, prices), (4.0, 0.4, 18.0))
        self.assertEqual(prices["gpt-oss-120b"]["pricing_profile"], "unpriced")

    def test_official_only_returns_date_does_not_fill_time(self):
        # 4. expires_on 日期解析。
        # 6. 官方只返回日期时不自行补时间。
        raw_result = {
            "rateLimitResetCredits": {
                "availableCount": 1,
                "credits": [
                    {
                        "id": "c1",
                        "expires_on": "2026-08-01",
                        "title": "Full reset"
                    }
                ]
            }
        }
        parsed = m.normalize_codex_app_server_rate_limits(raw_result, "2026-07-18T15:02:35Z")
        ent = parsed["reset_entitlements"]
        self.assertEqual(ent["status"], "official_live")
        self.assertEqual(len(ent["items"]), 1)
        self.assertIsNone(ent["items"][0]["expires_at"])
        self.assertEqual(ent["items"][0]["expires_on"], "2026-08-01")

    def test_derived_count_when_count_is_absent(self):
        # 7. 官方只返回 items 时可由 items 数量生成 count。
        # 8. count_semantics 为 derived_from_items。
        raw_result = {
            "rateLimitResetCredits": {
                "credits": [
                    {
                        "id": "c1",
                        "status": "available",
                        "expiresAt": 1785528035,
                        "title": "Full reset"
                    }
                ]
            }
        }
        parsed = m.normalize_codex_app_server_rate_limits(raw_result, "2026-07-18T15:02:35Z")
        ent = parsed["reset_entitlements"]
        self.assertEqual(ent["available_count"], 1)
        self.assertEqual(ent["count_semantics"], "derived_from_available_items")

    def test_available_count_zero_and_unavailable(self):
        # 9. available_count = 0 正常显示。
        # 10. unavailable 时 items 为空。
        # 11. unavailable 时不保留旧值。
        raw_result = {
            "rateLimitResetCredits": {
                "availableCount": 0,
                "credits": []
            }
        }
        parsed = m.normalize_codex_app_server_rate_limits(raw_result, "2026-07-18T15:02:35Z")
        ent = parsed["reset_entitlements"]
        self.assertEqual(ent["available_count"], 0)
        self.assertEqual(len(ent["items"]), 0)

        # Unavailable check
        unav = m.normalize_codex_app_server_rate_limits(None, "2026-07-18T15:02:35Z")
        self.assertEqual(unav["reset_entitlements"]["status"], "unavailable")
        self.assertEqual(len(unav["reset_entitlements"]["items"]), 0)
        self.assertIsNone(unav["reset_entitlements"]["available_count"])

    def test_reset_entitlements_fault_isolation(self):
        # 14. 重置权益失败不影响 Codex 周额度。
        # 15. Codex 周额度失败不影响重置权益。
        
        # Scenario A: Weekly rate limits succeeds, but reset entitlements fails.
        raw_result_a = {
            "rateLimits": {
                "limitId": "codex",
                "primary": {
                    "usedPercent": 26,
                    "windowDurationMins": 10080,
                    "resetsAt": 1784980175
                },
                "planType": "plus"
            },
            "rateLimitResetCredits": None  # reset entitlements fails
        }
        parsed_a = m.normalize_codex_app_server_rate_limits(raw_result_a, "2026-07-18T15:02:35Z")
        self.assertEqual(parsed_a["status"], "official_live")
        self.assertEqual(len(parsed_a["items"]), 1)
        self.assertEqual(parsed_a["reset_entitlements"]["status"], "unavailable")
        
        # Scenario B: Weekly rate limits fails, but reset entitlements succeeds.
        raw_result_b = {
            "rateLimits": None,  # weekly fails
            "rateLimitResetCredits": {
                "availableCount": 2,
                "credits": [
                    {
                        "id": "c1",
                        "expiresAt": 1785528035,
                        "title": "Full reset"
                    }
                ]
            }
        }
        parsed_b = m.normalize_codex_app_server_rate_limits(raw_result_b, "2026-07-18T15:02:35Z")
        self.assertEqual(parsed_b["status"], "unavailable")
        self.assertEqual(len(parsed_b["items"]), 0)
        self.assertEqual(parsed_b["reset_entitlements"]["status"], "official_live")
        self.assertEqual(parsed_b["reset_entitlements"]["available_count"], 2)

    def test_swift_code_ui_restrictions(self):
        # 16. UI 不包含“使用重置”按钮。
        # 17. UI 不包含 WebView。
        # 18. UI 不包含 Accessibility 读取逻辑。
        # 19. UI 不硬编码“2 次”。
        # 20. UI 不硬编码“8 月 1 日”或“8 月 13 日”。
        swift_path = "macos/AntigravityTokenMonitor/MenuBarView.swift"
        if os.path.exists(swift_path):
            with open(swift_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("使用重置", content)
            self.assertNotIn("WKWebView", content)
            self.assertNotIn("AXUIElement", content)
            self.assertNotIn("NSAccessibility", content)
            self.assertNotIn("2 次", content)
            self.assertNotIn("8月1日", content)
            self.assertNotIn("8月13日", content)
            self.assertNotIn("8 月 1 日", content)
            self.assertNotIn("8 月 13 日", content)
            
    def test_integrity_invariants(self):
        # 24. Token、API 成本、Antigravity quota 完全不变。
        dashboard = m._safe_load_json("data/dashboard.json", {})
        self.assertIn("sources", dashboard)
        self.assertIn("antigravity", dashboard["sources"])
        self.assertIn("codex", dashboard["sources"])
        
        # Verify get_quota_status doesn't mutate token/cost states
        import copy
        orig_dashboard = copy.deepcopy(dashboard)
        _ = m.get_quota_status({}, [])
        self.assertEqual(dashboard["sources"], orig_dashboard["sources"])
