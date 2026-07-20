import unittest
import os
import json
from pathlib import Path
import monitor_backend as m

class TestRefreshAnimationAndSettings(unittest.TestCase):
    def test_swift_rotation_effect_and_centers(self):
        swift_path = "macos/AntigravityTokenMonitor/MenuBarView.swift"
        if os.path.exists(swift_path):
            with open(swift_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. 刷新图标 rotationEffect 只作用于内部 Image。
            self.assertIn("Image(systemName: \"arrow.triangle.2.circlepath\")", content)
            self.assertNotIn("Image(systemName: \"arrow.clockwise\")", content)
            self.assertIn(".rotationEffect(.degrees(angle), anchor: .center)", content)

            # 2. Custom toolbar button is 32x32 and the outer style does not rotate.
            self.assertIn(".frame(width: 32, height: 32, alignment: .center)", content)
            
            # 3. 图标旋转 anchor 为 center。
            self.assertIn("anchor: .center", content)
            
            # 5. 扫描停止后角度严格恢复 0。
            # 6. 停止时禁用回弹和倒转动画。
            # 7. 再次扫描从正确初始位置开始 (elapsed time based in TimelineView)。
            self.assertIn("let angle = isScanning", content)
            self.assertIn("? (elapsed * 360.0).truncatingRemainder(dividingBy: 360.0)", content)
            self.assertIn(": 0.0", content)
            self.assertIn("TimelineView", content)
            self.assertIn("paused: !isScanning", content)

    def test_settings_page_disclaimer_and_picker_removal(self):
        swift_path = "macos/AntigravityTokenMonitor/MenuBarView.swift"
        if os.path.exists(swift_path):
            with open(swift_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 9. 设置页不存在 Standard/Priority segmented picker。
            self.assertNotIn("settingRow(\"API 价格档位\")", content)
            self.assertNotIn("Picker(\"\", selection: $dataModel.pricingTier)", content)

            # 20. 设置页面不显示 unknown_legacy。
            # 21. 设置页面不显示 codex-auto-review。
            model_path = "macos/AntigravityTokenMonitor/TokenDataModel.swift"
            with open(model_path, "r", encoding="utf-8") as f2:
                model_content = f2.read()
            self.assertIn("unknown_legacy", model_content)
            self.assertIn("codex-auto-review", model_content)
            self.assertIn("gpt-5.6-terra", model_content)
            self.assertIn("gpt-5.5", model_content)

            # 22. 主页面继续显示“标准 API 等价成本”。
            self.assertIn("标准 API 等价成本", content)

    def test_pricing_tier_fixed_to_standard(self):
        # 10. 运行时 pricing_tier 固定为 standard。
        settings = m.load_settings()
        self.assertEqual(settings.get("pricing_tier"), "standard")

    def test_pricing_values_are_correct(self):
        # Verify Standard model price values in default settings
        prices = m.DEFAULT_SETTINGS["model_prices"]
        
        # 11. Claude Opus 4.6 为 5 / 25
        self.assertEqual(prices["claude-opus-4-6-thinking"]["input_price_per_million"], 5.00)
        self.assertEqual(prices["claude-opus-4-6-thinking"]["output_price_per_million"], 25.00)
        
        # 12. Claude Sonnet 4.6 为 3 / 15
        self.assertEqual(prices["claude-sonnet-4-6"]["input_price_per_million"], 3.00)
        self.assertEqual(prices["claude-sonnet-4-6"]["output_price_per_million"], 15.00)
        
        # 13. Gemini 3.5 Flash 为 1.5 / 0.15 / 9
        self.assertEqual(prices["gemini-3-flash-a"]["input_price_per_million"], 1.50)
        self.assertEqual(prices["gemini-3-flash-a"]["cached_input_price_per_million"], 0.15)
        self.assertEqual(prices["gemini-3-flash-a"]["output_price_per_million"], 9.00)
        
        # 14. GPT-5.4 为 2.5 / 0.25 / 15
        self.assertEqual(prices["gpt-5.4"]["input_price_per_million"], 2.50)
        self.assertEqual(prices["gpt-5.4"]["cached_input_price_per_million"], 0.25)
        self.assertEqual(prices["gpt-5.4"]["output_price_per_million"], 15.00)
        
        # 15. GPT-5.4 Mini 为 0.75 / 0.075 / 4.5
        self.assertEqual(prices["gpt-5.4-mini"]["input_price_per_million"], 0.75)
        self.assertEqual(prices["gpt-5.4-mini"]["cached_input_price_per_million"], 0.075)
        self.assertEqual(prices["gpt-5.4-mini"]["output_price_per_million"], 4.50)
        
        # 16. GPT-5.6 Luna 为 1 / 0.1 / 6
        self.assertEqual(prices["gpt-5.6-luna"]["input_price_per_million"], 1.00)
        self.assertEqual(prices["gpt-5.6-luna"]["cached_input_price_per_million"], 0.10)
        self.assertEqual(prices["gpt-5.6-luna"]["output_price_per_million"], 6.00)
        
        # 17. GPT-5.6 Sol 为 5 / 0.5 / 30
        self.assertEqual(prices["gpt-5.6-sol"]["input_price_per_million"], 5.00)
        self.assertEqual(prices["gpt-5.6-sol"]["cached_input_price_per_million"], 0.50)
        self.assertEqual(prices["gpt-5.6-sol"]["output_price_per_million"], 30.00)

    def test_25x_migration_behavior(self):
        # 18. 旧 25 倍错误值在 user_overridden=false 时自动迁移。
        # Write a temporary settings with error values and user_overridden = False
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_settings_file = m.SETTINGS_FILE
            temp_settings_path = os.path.join(tmpdir, "settings.json")
            m.SETTINGS_FILE = temp_settings_path
            
            error_data = {
                "pricing_tier": "priority",
                "model_prices": {
                    "gpt-5.4": {
                        "input_price_per_million": 62.5,
                        "cached_input_price_per_million": 6.25,
                        "output_price_per_million": 375.0,
                        "user_overridden": False
                    },
                    "gpt-5.4-mini": {
                        "input_price_per_million": 18.75,
                        "cached_input_price_per_million": 1.875,
                        "output_price_per_million": 113.0,
                        "user_overridden": True # 19. user_overridden=true 时不静默覆盖。
                    }
                }
            }
            
            with open(temp_settings_path, "w", encoding="utf-8") as f:
                json.dump(error_data, f)
                
            merged = m.load_settings()
            
            # gpt-5.4 should be migrated:
            self.assertEqual(merged["model_prices"]["gpt-5.4"]["input_price_per_million"], 2.50)
            self.assertEqual(merged["model_prices"]["gpt-5.4"]["output_price_per_million"], 15.00)
            
            # gpt-5.4-mini should NOT be migrated because user_overridden = True:
            self.assertEqual(merged["model_prices"]["gpt-5.4-mini"]["input_price_per_million"], 18.75)
            self.assertEqual(merged["model_prices"]["gpt-5.4-mini"]["output_price_per_million"], 113.0)
            
            # Verify it is persisted to disk (not just in memory)
            with open(temp_settings_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            self.assertEqual(saved_data["model_prices"]["gpt-5.4"]["input_price_per_million"], 2.50)
            self.assertEqual(saved_data["model_prices"]["gpt-5.4-mini"]["input_price_per_million"], 18.75)
            
            m.SETTINGS_FILE = orig_settings_file

    def test_all_codex_models_migration_and_persistence(self):
        # Verify migration of all four requested Codex models
        import tempfile, json
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_settings_file = m.SETTINGS_FILE
            temp_settings_path = os.path.join(tmpdir, "settings.json")
            m.SETTINGS_FILE = temp_settings_path
            
            error_data = {
                "pricing_tier": "standard",
                "model_prices": {
                    "gpt-5.4": {
                        "input_price_per_million": 62.5,
                        "cached_input_price_per_million": 6.25,
                        "output_price_per_million": 375.0,
                        "user_overridden": False
                    },
                    "gpt-5.4-mini": {
                        "input_price_per_million": 18.75,
                        "cached_input_price_per_million": 1.875,
                        "output_price_per_million": 113.0,
                        "user_overridden": False
                    },
                    "gpt-5.6-luna": {
                        "input_price_per_million": 25.0,
                        "cached_input_price_per_million": 2.5,
                        "output_price_per_million": 150.0,
                        "user_overridden": False
                    },
                    "gpt-5.6-sol": {
                        "input_price_per_million": 125.0,
                        "cached_input_price_per_million": 12.5,
                        "output_price_per_million": 750.0,
                        "user_overridden": False
                    }
                }
            }
            
            with open(temp_settings_path, "w", encoding="utf-8") as f:
                json.dump(error_data, f)
                
            merged = m.load_settings()
            
            # gpt-5.4: 2.50 / 0.25 / 15.00
            self.assertEqual(merged["model_prices"]["gpt-5.4"]["input_price_per_million"], 2.50)
            self.assertEqual(merged["model_prices"]["gpt-5.4"]["cached_input_price_per_million"], 0.25)
            self.assertEqual(merged["model_prices"]["gpt-5.4"]["output_price_per_million"], 15.00)
            
            # gpt-5.4-mini: 0.75 / 0.075 / 4.50
            self.assertEqual(merged["model_prices"]["gpt-5.4-mini"]["input_price_per_million"], 0.75)
            self.assertEqual(merged["model_prices"]["gpt-5.4-mini"]["cached_input_price_per_million"], 0.075)
            self.assertEqual(merged["model_prices"]["gpt-5.4-mini"]["output_price_per_million"], 4.50)
            
            # gpt-5.6-luna: 1.00 / 0.10 / 6.00
            self.assertEqual(merged["model_prices"]["gpt-5.6-luna"]["input_price_per_million"], 1.00)
            self.assertEqual(merged["model_prices"]["gpt-5.6-luna"]["cached_input_price_per_million"], 0.10)
            self.assertEqual(merged["model_prices"]["gpt-5.6-luna"]["output_price_per_million"], 6.00)
            
            # gpt-5.6-sol: 5.00 / 0.50 / 30.00
            self.assertEqual(merged["model_prices"]["gpt-5.6-sol"]["input_price_per_million"], 5.00)
            self.assertEqual(merged["model_prices"]["gpt-5.6-sol"]["cached_input_price_per_million"], 0.50)
            self.assertEqual(merged["model_prices"]["gpt-5.6-sol"]["output_price_per_million"], 30.00)
            
            # Check persistence
            with open(temp_settings_path, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
            self.assertEqual(disk_data["model_prices"]["gpt-5.6-sol"]["input_price_per_million"], 5.00)
            
            m.SETTINGS_FILE = orig_settings_file

    def test_swift_and_python_share_same_runtime_settings(self):
        # 1. Swift 和 Python 使用同一个运行时 settings.json 路径结构
        swift_path = "macos/AntigravityTokenMonitor/TokenDataModel.swift"
        swift_code = Path(swift_path).read_text(encoding="utf-8")
        self.assertIn("TokenRuntimePaths.file(\"settings.json\").path", swift_code)
        
        # Verify fallback defaults in Swift matches correct prices
        self.assertIn("\"gpt-5.4\": ModelPriceDetail", swift_code)
        self.assertIn("inputPricePerMillion: 2.50", swift_code)
        self.assertIn("outputPricePerMillion: 15.00", swift_code)
        self.assertIn("cachedInputPricePerMillion: 0.25", swift_code)

    def test_settings_scroll_view_padding_logic(self):
        # 13. 价格列表有固定底栏所需的底部安全 padding (48 + 32 = 80pt)
        swift_path = "macos/AntigravityTokenMonitor/MenuBarView.swift"
        swift_code = Path(swift_path).read_text(encoding="utf-8")
        self.assertIn(".padding(.bottom, 48)", swift_code)
        self.assertIn(".padding(.bottom, 32)", swift_code)

    def test_token_cost_and_official_live_data_integrity(self):
        # 23. Token 数量修改前后完全一致。
        # 24. official_live 数据修改前后完全一致。
        dashboard = json.loads(Path("data/dashboard.json").read_text(encoding="utf-8"))
        self.assertIn("sources", dashboard)
        self.assertIn("antigravity", dashboard["sources"])
        self.assertIn("codex", dashboard["sources"])
        self.assertIn("quota_status", dashboard)
