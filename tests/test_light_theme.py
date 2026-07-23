import json
import unittest
from pathlib import Path


MENU = Path("macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
MODEL = Path("macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
CACHE = Path("macos/AntigravityTokenMonitor/TokenCacheReader.swift").read_text(encoding="utf-8")
CLI = Path("cli/quotaview_cli.py").read_text(encoding="utf-8")


class TestLightTheme(unittest.TestCase):
    def test_system_theme_does_not_force_dark(self):
        self.assertIn("case .system: return nil", MODEL)
        self.assertNotIn("preferredColorScheme(.dark)", MENU)

    def test_light_theme_forces_light(self):
        self.assertIn("case .light:  return .light", MODEL)

    def test_dark_theme_forces_dark(self):
        self.assertIn("case .dark:   return .dark", MODEL)

    def test_root_uses_palette_background(self):
        self.assertIn("palette.windowBackground", MENU)

    def test_title_uses_palette_primary_text(self):
        self.assertIn('Text("QuotaView").font(.system(size: 12, weight: .bold))', MENU)
        self.assertIn(".foregroundColor(palette.primaryText)", MENU)

    def test_inactive_segment_uses_palette_text(self):
        self.assertIn("palette.inactiveSegmentText", MENU)

    def test_selected_segment_uses_palette_background_and_text(self):
        self.assertIn("palette.selectedSegmentBackground", MENU)
        self.assertIn("palette.selectedSegmentText", MENU)

    def test_token_cards_use_palette(self):
        self.assertIn(".background(palette.cardBackground)", MENU)
        self.assertIn(".stroke(palette.border", MENU)

    def test_settings_title_is_themeable(self):
        self.assertIn('dataModel.tr("设置", "Settings")', MENU)

    def test_settings_labels_are_not_hardcoded_black(self):
        self.assertNotIn("foregroundColor(.black)", MENU)
        self.assertNotIn("Color.black", MENU)

    def test_settings_labels_are_not_hardcoded_white(self):
        self.assertNotIn("foregroundColor(.white)", MENU)
        self.assertNotIn("Color.white", MENU)

    def test_price_model_names_are_themeable(self):
        self.assertIn("Text(detail.displayName)", MENU)
        self.assertIn("palette.primaryText", MENU)

    def test_price_labels_are_themeable(self):
        self.assertIn('dataModel.tr("输入", "Input")', MENU)
        self.assertIn('dataModel.tr("输出", "Output")', MENU)

    def test_price_inputs_use_themeable_surface_and_text(self):
        self.assertIn(".background(palette.inputBackground)", MENU)
        self.assertIn(".foregroundColor(palette.primaryText)", MENU)

    def test_divider_uses_palette(self):
        self.assertIn("Divider().background(palette.divider)", MENU)

    def test_footer_icons_use_themeable_color(self):
        self.assertIn("secondaryLabelColor", MENU)
        self.assertIn('systemName: "gearshape"', MENU)

    def test_destructive_buttons_have_light_dark_configuration(self):
        self.assertIn("destructiveText", MENU)
        self.assertIn("destructiveBackground", MENU)
        self.assertIn("systemRed", MENU)

    def test_progress_uses_system_colors(self):
        self.assertIn("systemBlue", MENU)
        self.assertIn("systemOrange", MENU)
        self.assertIn("systemRed", MENU)

    def test_progress_track_has_theme_configuration(self):
        self.assertIn("progressTrack", MENU)
        self.assertIn("Color(nsColor: .quaternaryLabelColor)", MENU)

    def test_progress_thresholds_remain_50_and_80(self):
        self.assertIn("clamped >= 80.0", MENU)
        self.assertIn("clamped >= 50.0", MENU)

    def test_inactive_labels_are_not_system_primary_on_dark_surface(self):
        self.assertIn("segmentTrackBackground", MENU)
        self.assertNotIn(".background(Color.black", MENU)

    def test_gemini_default_hidden_from_settings(self):
        self.assertIn('"gemini-default"', MODEL)
        self.assertIn('"unknown_legacy", "codex-auto-review", "gemini-default"', MODEL)

    def test_gemini_default_not_in_default_cli_prices(self):
        self.assertNotIn("gemini-default", CLI.split("def resolved_pricing_data", 1)[0])

    def test_dark_palette_structure_remains(self):
        for field in ("windowBackground", "cardBackground", "elevatedBackground", "primaryText", "secondaryText", "progressTrack"):
            self.assertIn(f"let {field}: Color", MENU)

    def test_palette_is_single_source(self):
        self.assertIn("struct QuotaViewPalette", MENU)
        self.assertIn("private var palette: QuotaViewPalette", MENU)

    def test_theme_updates_from_published_setting(self):
        self.assertIn(".preferredColorScheme(dataModel.theme.colorScheme)", MENU)

    def test_token_cost_quota_data_models_are_not_touched_by_theme(self):
        self.assertIn("@Published var dashboard = LightDashboard.empty", MODEL)
        self.assertIn("quotaStatus", CACHE)
        self.assertIn("estimatedCost", CACHE)

    def test_cli_schema_unchanged(self):
        self.assertIn('SCHEMA_VERSION = 1', CLI)

    def test_application_support_path_not_in_theme_view(self):
        self.assertNotIn("Documents/Antigravity", MENU)

    def test_light_segment_track_is_near_white(self):
        self.assertIn("segmentTrackBackground", MENU)
        self.assertIn(".textBackgroundColor", MENU)

    def test_segment_has_no_gray_or_dark_track(self):
        self.assertNotIn("Color.gray", MENU)
        self.assertNotIn("segmentTrackBackground = Color.black", MENU)

    def test_segment_selected_uses_light_accent(self):
        self.assertIn("selectedSegmentBorder", MENU)
        self.assertIn("controlAccentColor", MENU)

    def test_segment_unselected_is_transparent(self):
        self.assertIn("isSelected ? palette.selectedSegmentBackground : Color.clear", MENU)

    def test_dark_segment_configuration_exists(self):
        self.assertIn("light ? .controlBackgroundColor : .underPageBackgroundColor", MENU)

    def test_theme_picker_binds_published_theme(self):
        self.assertIn("selection: $dataModel.theme", MENU)

    def test_settings_json_persists_theme(self):
        self.assertIn('var theme: String?', MODEL)
        self.assertIn('case theme', MODEL)
        self.assertIn('theme: theme.rawValue', MODEL)

    def test_apply_appearance_is_single_method(self):
        self.assertIn("func applyAppearance()", MODEL)
        self.assertEqual(MODEL.count("func applyAppearance()"), 1)

    def test_system_maps_to_nil_appearance(self):
        self.assertIn("case .system:", MODEL)
        self.assertIn("appearance = nil", MODEL)

    def test_light_maps_to_aqua(self):
        self.assertIn("appearance = NSAppearance(named: .aqua)", MODEL)

    def test_dark_maps_to_dark_aqua(self):
        self.assertIn("appearance = NSAppearance(named: .darkAqua)", MODEL)

    def test_theme_change_applies_appearance(self):
        theme_block = MODEL[MODEL.index('@Published var theme'):MODEL.index('@Published var scanOnStartup')]
        self.assertIn("applyAppearance()", theme_block)

    def test_root_rebuilds_for_theme(self):
        self.assertIn(".id(dataModel.theme.rawValue)", MENU)

    def test_palette_uses_effective_color_scheme(self):
        self.assertIn("private var effectiveColorScheme: ColorScheme", MENU)
        self.assertIn("case .dark: return .dark", MENU)
        self.assertIn("QuotaViewPalette(colorScheme: effectiveColorScheme)", MENU)

    def test_save_applies_appearance_immediately(self):
        self.assertNotIn('Button("保存")', MENU)
        self.assertIn("applyAppearance()", MODEL)

    def test_startup_applies_saved_theme(self):
        init_block = MODEL[MODEL.index('init() {'):MODEL.index('// MARK: - Computed stats')]
        self.assertIn("loadSettingsFile()", init_block)
        self.assertIn("applyAppearance()", init_block)

    def test_reset_defaults_applies_system_theme(self):
        reset_block = MENU[MENU.index('private func resetDefaults()'):MENU.index('\n    }\n}', MENU.index('private func resetDefaults()'))]
        self.assertIn("dataModel.theme           = .system", reset_block)

    def test_menu_bar_content_reapplies_theme_on_appear(self):
        app = Path("macos/AntigravityTokenMonitor/AntigravityTokenMonitorApp.swift").read_text(encoding="utf-8")
        self.assertIn("dataModel.applyAppearance()", app)


if __name__ == "__main__":
    unittest.main()
