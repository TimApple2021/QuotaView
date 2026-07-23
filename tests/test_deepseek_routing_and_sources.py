"""Unit tests covering QuotaView Section 7 DeepSeek routing, DisplayedSources enum, and Keychain security rules.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift"
VIEW_PATH = ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift"
BACKEND_PATH = ROOT / "deepseek_backend.py"
CLI_PATH = ROOT / "cli/quotaview_cli.py"

MODEL = MODEL_PATH.read_text(encoding="utf-8")
VIEW = VIEW_PATH.read_text(encoding="utf-8")
BACKEND = BACKEND_PATH.read_text(encoding="utf-8")
CLI = CLI_PATH.read_text(encoding="utf-8")


class TestDeepSeekRoutingAndSources(unittest.TestCase):

    # 1. PopoverPage contains only the pages with real routes
    def test_01_popover_page_enum_cases(self):
        self.assertIn("enum PopoverPage { case dashboard, settings, deepseekSettings }", VIEW)
        self.assertNotIn("pricing", VIEW[VIEW.index("enum PopoverPage"):VIEW.index("enum PopoverPage") + 100])

    # 2. MenuBarView.body 显式路由 (非 fallback else)
    def test_02_menu_bar_view_body_explicit_switch_routing(self):
        self.assertIn("switch page {", VIEW)
        self.assertIn("case .dashboard:\n                dashboardPage", VIEW)
        self.assertIn("case .settings:\n                settingsPage", VIEW)
        self.assertIn("case .deepseekSettings:\n                deepseekSettingsPage", VIEW)


    # 3. AISource 包含 deepseek 数据源
    def test_03_ai_source_has_deepseek(self):
        self.assertIn("case deepseek    = \"DeepSeek\"", MODEL)
        self.assertIn("case .deepseek:    return \"deepseek\"", MODEL)

    # 4. DeepSeek 处于 dashboardContent 分支中
    def test_04_deepseek_is_inside_dashboard_content(self):
        self.assertIn("switch dataModel.selectedSource {", VIEW)
        self.assertIn("case .deepseek:\n                        deepseekDashboardContent", VIEW)

    # 5. 齿轮进入 settings
    def test_05_gear_button_enters_settings(self):
        self.assertIn("page = .settings", VIEW)

    # 6. 顶部存在 Antigravity | Codex | DeepSeek 三个入口
    def test_06_top_segmented_control_has_three_segments(self):
        self.assertIn('sourceSegment(label: "Antigravity", source: .antigravity)', VIEW)
        self.assertIn('sourceSegment(label: "Codex", source: .codex)', VIEW)
        self.assertIn('sourceSegment(label: "DeepSeek", source: .deepseek)', VIEW)

    # 7. 底部 Toolbar 在所有 3 个数据源下都存在
    def test_07_bottom_bar_always_present(self):
        self.assertIn("dataModel.refreshCurrentSource()", VIEW)
        self.assertIn("Image(systemName: \"gearshape\")", VIEW)

    # 8. DeepSeek 主数据展示页中没有 SecureField / 保存 Key / 导入 ZIP 按钮
    def test_08_deepseek_dashboard_content_is_pure_presentation(self):
        start = VIEW.index("private var deepseekDashboardContent: some View")
        end = VIEW.index("private var deepseekSettingsPage: some View", start)
        block = VIEW[start:end]
        self.assertNotIn("SecureField", block)
        self.assertNotIn("dataModel.saveDeepSeekApiKey", block)
        self.assertNotIn("selectAndImportDeepSeekZip()", block)
        self.assertIn("Official Live Balance", block)
        self.assertIn("Exported Usage History", block)

    # 9. DeepSeek 配置位于 settings 页面
    def test_09_deepseek_settings_page_contains_configuration(self):
        start = VIEW.index("private var deepseekSettingsPage: some View")
        block = VIEW[start:]
        self.assertIn("SecureField", block)
        self.assertIn("dataModel.saveDeepSeekApiKey", block)
        self.assertIn("selectAndImportDeepSeekZip()", block)

    # 10. DisplayedSources 包含四项
    def test_10_displayed_sources_has_four_cases(self):
        self.assertIn("case all", MODEL)
        self.assertIn("case antigravityOnly", MODEL)
        self.assertIn("case codexOnly", MODEL)
        self.assertIn("case deepseekOnly", MODEL)

    # 11. 仅 DeepSeek 模式绑定 selectedSource = .deepseek
    def test_11_deepseek_only_binds_deepseek_source(self):
        self.assertIn("case .deepseekOnly:\n            if selectedSource != .deepseek { selectedSource = .deepseek }", MODEL)

    # 12. 旧 both 设置迁移为 all
    def test_12_legacy_both_setting_migrates_to_all(self):
        self.assertIn('case "all", "both", "combined":', MODEL)
        self.assertIn("return .all", MODEL)

    # 13. 中文文案包含 全部 / 仅 Antigravity / 仅 Codex / 仅 DeepSeek
    def test_13_chinese_labels(self):
        self.assertIn('case .all: return tr("全部", "All")', MODEL)
        self.assertIn('case .antigravityOnly: return tr("仅 Antigravity", "Antigravity Only")', MODEL)
        self.assertIn('case .codexOnly: return tr("仅 Codex", "Codex Only")', MODEL)
        self.assertIn('case .deepseekOnly: return tr("仅 DeepSeek", "DeepSeek Only")', MODEL)

    # 14. 菜单栏由 selectedSource 分派，DeepSeek 费用不与其他来源相加
    def test_14_cny_usd_currency_isolation(self):
        update = MODEL[MODEL.index("func updateMenuBarText()"):MODEL.index("private func formatMenuBarForSourceStats")]
        self.assertIn("switch selectedSource", update)
        self.assertNotIn("formatMenuBarForAll", MODEL)
        self.assertIn('let sym = (curr == "USD") ? "$" : "¥"', MODEL)

    # 15. 零 Keychain 调用断言
    def test_15_zero_keychain_in_entire_codebase(self):
        for code in (MODEL, VIEW, BACKEND, CLI):
            self.assertNotIn("SecItemAdd", code)
            self.assertNotIn("SecItemCopyMatching", code)
            self.assertNotIn("SecItemDelete", code)
            self.assertNotIn("DeepSeekKeychain", code)
            self.assertNotIn("deepseek_api_key_native_v2", code)
            self.assertNotIn("/usr/bin/security", code)

    # 16. 私有 Credential Store 接口断言
    def test_16_credential_store_used(self):
        self.assertIn("DeepSeekCredentialStore.save", MODEL)
        self.assertIn("DeepSeekCredentialStore.load", MODEL)
        self.assertIn("DeepSeekCredentialStore.delete", MODEL)
        self.assertIn("DeepSeekCredentialStore.isConfigured", MODEL)

    # 18. 设置主页绝对包含 DeepSeek 配置入口按钮
    def test_18_settings_page_has_deepseek_entrance(self):
        settings_start = VIEW.index("private var settingsPage")
        settings_end = VIEW.index("private var deepseekDashboardContent")
        settings_code = VIEW[settings_start:settings_end]
        self.assertIn('settingRow(dataModel.tr("DeepSeek 配置", "DeepSeek Settings"))', settings_code)
        self.assertIn("page = .deepseekSettings", settings_code)
        self.assertIn('dataModel.tr("已配置", "Configured")', settings_code)
        self.assertIn('dataModel.tr("未配置", "Not Configured")', settings_code)


if __name__ == "__main__":
    unittest.main()
