import plistlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLED_APP = Path("/Applications/QuotaView.app")
BUILD = (ROOT / "macos/build.sh").read_text(encoding="utf-8")
SWIFT_DIR = ROOT / "macos/AntigravityTokenMonitor"
SWIFT = "\n".join(path.read_text(encoding="utf-8") for path in SWIFT_DIR.glob("*.swift"))


class TestQuotaViewBranding(unittest.TestCase):
    def test_final_application_name_is_quotaview(self):
        self.assertIn('APP_NAME="QuotaView"', BUILD)

    def test_info_plist_display_name_is_quotaview(self):
        self.assertRegex(BUILD, r"<key>CFBundleDisplayName</key>\s*<string>QuotaView</string>")

    def test_bundle_identifier_is_preserved(self):
        self.assertIn("com.antigravity.tokenmonitor", BUILD)

    def test_executable_name_is_quotaview(self):
        self.assertIn('EXECUTABLE_NAME="QuotaView"', BUILD)
        self.assertRegex(BUILD, r"<key>CFBundleExecutable</key>\s*<string>QuotaView</string>")

    def test_icns_exists_and_is_nonempty(self):
        icon = ROOT / "branding/QuotaView/QuotaView.icns"
        self.assertTrue(icon.is_file())
        self.assertGreater(icon.stat().st_size, 100_000)

    def test_icns_is_configured_and_bundled(self):
        self.assertRegex(BUILD, r"<key>CFBundleIconFile</key>\s*<string>QuotaView\.icns</string>")
        self.assertIn('QuotaView.icns" "$RES_DIR/QuotaView.icns', BUILD)

    def test_menu_bar_no_longer_uses_flying_saucer_emoji(self):
        self.assertNotIn("🛸", SWIFT)

    def test_header_no_longer_says_ai_token_monitor(self):
        self.assertNotIn('Text("AI Token Monitor")', SWIFT)
        self.assertIn('Text("QuotaView")', SWIFT)

    def test_antigravity_data_source_name_remains(self):
        self.assertIn('case antigravity = "Antigravity"', SWIFT)

    def test_legacy_application_support_path_is_preserved(self):
        self.assertIn('appendingPathComponent("Antigravity Token Monitor"', SWIFT)
        self.assertIn('Application Support/Antigravity Token Monitor', BUILD)

    def test_build_installs_quotaview_in_applications(self):
        self.assertIn('GLOBAL_DEST="/Applications/$APP_NAME.app"', BUILD)
        self.assertNotIn('APP_NAME="Antigravity Token Monitor"', BUILD)

    def test_old_history_is_never_overwritten_during_compatibility_migration(self):
        self.assertIn('[ ! -e "$SUPPORT_DIR/$file" ]', BUILD)
        self.assertNotIn('rm -rf "$SUPPORT_DIR"', BUILD)

    def test_template_icon_is_marked_template(self):
        brand = (SWIFT_DIR / "BrandAssets.swift").read_text(encoding="utf-8")
        self.assertIn("isTemplate: true", brand)
        self.assertIn("image.isTemplate = isTemplate", brand)

    def test_menu_and_header_resources_are_bundled(self):
        for name in ("QuotaViewMenuTemplate-18@2x.png", "QuotaViewHeader-18@2x.png"):
            self.assertIn(name, BUILD)

    def test_installed_bundle_has_final_name_and_executable(self):
        with (INSTALLED_APP / "Contents/Info.plist").open("rb") as handle:
            info = plistlib.load(handle)
        self.assertEqual(info["CFBundleName"], "QuotaView")
        self.assertEqual(info["CFBundleDisplayName"], "QuotaView")
        self.assertEqual(info["CFBundleExecutable"], "QuotaView")

    def test_installed_bundle_contains_icns_and_template_resources(self):
        resources = INSTALLED_APP / "Contents/Resources"
        for name in ("QuotaView.icns", "QuotaViewMenuTemplate-18@2x.png", "QuotaViewHeader-18@2x.png"):
            self.assertTrue((resources / name).is_file(), name)

    def test_old_installed_application_is_absent(self):
        self.assertFalse(Path("/Applications/Antigravity Token Monitor.app").exists())


if __name__ == "__main__":
    unittest.main()
