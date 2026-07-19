from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
VIEW = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
BUILD = (ROOT / "macos/build.sh").read_text(encoding="utf-8")


def test_language_setting_is_persisted_and_has_two_options():
    assert 'enum AppLanguage: String, CaseIterable, Identifiable' in MODEL
    assert 'case chinese = "中文"' in MODEL
    assert 'case english = "English"' in MODEL
    assert 'forKey: "language"' in MODEL
    assert 'Text("中文").tag(AppLanguage.chinese)' in VIEW
    assert 'Text("English").tag(AppLanguage.english)' in VIEW


def test_main_ui_has_bilingual_localization_entries():
    assert 'dataModel.tr("模型输入", "Input Tokens")' in VIEW
    assert 'dataModel.tr("额度监控", "Quota Monitoring")' in VIEW
    assert 'dataModel.tr("设置", "Settings")' in VIEW
    assert 'dataModel.tr("使用限额重置", "Usage Limit Resets")' in VIEW


def test_readme_is_bilingual():
    assert "## English" in README
    assert "## 中文" in README
    assert "Chinese and English UI selectable in Settings" in README
    assert "设置页可选择中文或 English" in README


def test_release_build_version_is_bumped():
    assert 'VERSION="1.0.2"' in BUILD
