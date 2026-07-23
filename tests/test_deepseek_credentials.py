"""Unit tests covering DeepSeekCredentialStore file security, permissions, and credential isolation.
"""

import os
import stat
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWIFT_STORE_PATH = ROOT / "macos/AntigravityTokenMonitor/DeepSeekCredentialStore.swift"
APP_RESOURCES_PATH = ROOT / "QuotaView.app/Contents/Resources"


class TestDeepSeekCredentialStore(unittest.TestCase):

    def test_01_swift_credential_store_file_exists(self):
        self.assertTrue(SWIFT_STORE_PATH.is_file())

    def test_02_swift_credential_store_uses_atomic_write_and_chmod(self):
        code = SWIFT_STORE_PATH.read_text(encoding="utf-8")
        self.assertIn("0o700", code)
        self.assertIn("0o600", code)
        self.assertIn("deepseek_credentials.json.tmp", code)
        self.assertIn("deepseek_credentials.json", code)

    def test_03_zero_keychain_security_in_credential_store(self):
        code = SWIFT_STORE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("SecItem", code)
        self.assertNotIn("kSecClass", code)
        self.assertNotIn("Security.framework", code)

    def test_04_credentials_json_is_not_in_app_resources(self):
        if APP_RESOURCES_PATH.exists():
            for p in APP_RESOURCES_PATH.rglob("*"):
                self.assertNotEqual(p.name, "deepseek_credentials.json")

    def test_05_credentials_json_is_not_in_settings_or_dashboard(self):
        app_supp = Path.home() / "Library/Application Support/Antigravity Token Monitor"
        cred_path = app_supp / "deepseek_credentials.json"
        if cred_path.exists():
            st = cred_path.stat()
            mode = stat.S_IMODE(st.st_mode)
            # Verify file permission is 0600 (read/write by owner only)
            self.assertEqual(mode, 0o600)

            dash_path = app_supp / "dashboard.json"
            sett_path = app_supp / "settings.json"
            raw_key = ""
            try:
                raw_key = json.loads(cred_path.read_text(encoding="utf-8")).get("api_key", "")
            except (OSError, ValueError, AttributeError):
                pass
            if dash_path.exists():
                dash_text = dash_path.read_text(encoding="utf-8")
                # Masked identity metadata is safe for display; raw keys must
                # never be present in runtime snapshots.
                if raw_key:
                    self.assertNotIn(raw_key, dash_text)
            if sett_path.exists():
                sett_text = sett_path.read_text(encoding="utf-8")
                if raw_key:
                    self.assertNotIn(raw_key, sett_text)


if __name__ == "__main__":
    unittest.main()
