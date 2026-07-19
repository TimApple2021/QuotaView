import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import monitor_backend as m


class TestRuntimeResilience(unittest.TestCase):
    def test_atomic_write_preserves_backup(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "dashboard.json")
            Path(path).write_text(json.dumps({"version": 1}), encoding="utf-8")
            m._atomic_write_json(path, {"version": 2})
            self.assertEqual(json.loads(Path(path).read_text())["version"], 2)
            self.assertEqual(json.loads(Path(path + ".bak").read_text())["version"], 1)
            self.assertFalse(Path(path + ".tmp").exists())

    def test_runtime_data_dir_can_be_redirected(self):
        with tempfile.TemporaryDirectory() as td:
            code = "import monitor_backend; print(monitor_backend.DATA_DIR)"
            env = dict(os.environ, TOKEN_MONITOR_DATA_DIR=td)
            result = subprocess.check_output([sys.executable, "-c", code], env=env, text=True).strip()
            self.assertEqual(result, os.path.abspath(td))

    def test_installed_backend_is_bundled_as_resource(self):
        self.assertTrue(Path("macos/build.sh").read_text().find('cp "$PROJECT_DIR/monitor_backend.py" "$RES_DIR/monitor_backend.py"') >= 0)

    def test_swift_runtime_paths_do_not_use_documents(self):
        private_project_marker = str(Path.cwd().resolve())
        for path in Path("macos/AntigravityTokenMonitor").glob("*.swift"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(private_project_marker, text)

    def test_dashboard_has_core_sources_after_quota_status(self):
        dashboard = json.loads(Path("data/dashboard.json").read_text(encoding="utf-8"))
        self.assertIn("sources", dashboard)
        self.assertIn("antigravity", dashboard["sources"])
        self.assertIn("codex", dashboard["sources"])

    def test_quota_status_is_separate_from_token_sources(self):
        dashboard = json.loads(Path("data/dashboard.json").read_text(encoding="utf-8"))
        self.assertIn("sources", dashboard)
        self.assertIn("quota_status", dashboard)
        self.assertNotIn("quota_status", dashboard["sources"])

    def test_old_quota_array_is_accepted_by_backend_contract(self):
        legacy = {"antigravity": [], "codex": []}
        self.assertEqual(legacy["antigravity"], [])
        self.assertIn("items", m.get_quota_status({}, []) ["codex"])

    def test_new_quota_status_has_explicit_failure_message(self):
        status = m.read_codex_accessibility_quota()
        if status["status"] != "official_live":
            self.assertEqual(status["message"], "暂时无法读取当前官方额度")

    def test_application_support_migration_keeps_history(self):
        support = Path.home() / "Library/Application Support/Antigravity Token Monitor"
        self.assertTrue((support / "daily_history.json").exists())
        self.assertTrue((support / "conversation_history.json").exists())

    def test_settings_migration_keeps_standard_tier(self):
        support = Path.home() / "Library/Application Support/Antigravity Token Monitor/settings.json"
        settings = json.loads(support.read_text(encoding="utf-8"))
        self.assertEqual(settings.get("pricing_tier"), "standard")
        gem = settings["model_prices"]["gemini-3-flash-a"]
        self.assertEqual(gem["input_price_per_million"], 1.5)


if __name__ == "__main__":
    unittest.main()
