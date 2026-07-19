from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
VIEW = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
CLI = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")
BACKEND = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_old_settings_default_to_both():
    assert "@Published var displayedSources: DisplayedSources = .both" in MODEL
    assert 'forKey: "displayedSources"' in MODEL


def test_displayed_sources_has_three_mutually_exclusive_values():
    assert "case both" in MODEL
    assert "case antigravityOnly" in MODEL
    assert "case codexOnly" in MODEL
    assert "Toggle" not in MODEL[MODEL.index("enum DisplayedSources"):MODEL.index("// MARK: - TokenDataModel")]


def test_both_shows_segment():
    assert "var shouldShowSourceSegment: Bool { displayedSources == .both }" in MODEL
    assert "if dataModel.shouldShowSourceSegment" in VIEW
    assert "sourceSegmentedControl" in VIEW


def test_antigravity_only_hides_segment_and_selects_antigravity():
    assert "case .antigravityOnly" in MODEL
    assert "selectedSource = .antigravity" in MODEL
    assert "displayedSources == .both" in MODEL


def test_codex_only_hides_segment_and_selects_codex():
    assert "case .codexOnly" in MODEL
    assert "selectedSource = .codex" in MODEL


def test_switching_back_to_both_restores_segment_without_forcing_source():
    block = MODEL[MODEL.index("private func enforceDisplayedSourceSelection"):MODEL.index("func refreshIntervalLabel")]
    assert "case .both: break" in block
    assert "shouldShowSourceSegment" in MODEL


def test_single_source_mode_has_no_segment_padding_wrapper():
    start = VIEW.index("if dataModel.shouldShowSourceSegment")
    end = VIEW.index("// Stat cards", start)
    block = VIEW[start:end]
    assert ".padding(.top, 10)" in block
    assert "if dataModel.shouldShowSourceSegment" in block


def test_menu_bar_uses_selected_source_stats():
    assert "dashboard.sources[selectedSource.jsonKey]" in MODEL
    assert "updateMenuBarText()" in MODEL[MODEL.index("@Published var displayedSources"):MODEL.index("@Published var refreshInterval")]


def test_displayed_sources_is_immediately_persisted_to_both_stores():
    assert 'UserDefaults.standard.set(displayedSources.rawValue, forKey: "displayedSources")' in MODEL
    assert 'displayedSources: displayedSources.rawValue' in MODEL
    assert 'displayedSources = "displayed_sources"' in MODEL


def test_app_restart_restores_displayed_sources():
    assert 'ud.string(forKey: "displayedSources")' in MODEL
    assert "config.displayedSources" in MODEL


def test_restore_defaults_returns_to_both():
    reset = VIEW[VIEW.index("private func resetDefaults"):VIEW.index("struct RefreshButtonIcon")]
    assert "dataModel.displayedSources = .both" in reset


def test_chinese_labels():
    assert '"Antigravity 与 Codex"' in MODEL
    assert '"仅 Antigravity"' in MODEL
    assert '"仅 Codex"' in MODEL
    assert '"显示来源"' in VIEW


def test_english_labels():
    assert '"Antigravity & Codex"' in MODEL
    assert '"Antigravity Only"' in MODEL
    assert '"Codex Only"' in MODEL
    assert '"Displayed Sources"' in VIEW


def test_cli_still_supports_both_sources_and_schema_one():
    assert "SCHEMA_VERSION = 1" in CLI
    assert 'return ["antigravity", "codex"]' in CLI
    assert 'CURRENT_AG' in CLI and 'CURRENT_CODEX' in CLI


def test_backend_scan_scope_is_unchanged_and_covers_both_sources():
    assert "def scan_codex_conversations" in BACKEND
    assert "def scan_conversations" in BACKEND
    assert "app_data_dirs" in BACKEND
    assert "daily_history" in BACKEND


def test_displayed_sources_does_not_add_token_or_cost_calculation():
    assert "identifiableTokens" not in MODEL[MODEL.index("enum DisplayedSources"):MODEL.index("// MARK: - TokenDataModel")]
    assert "estimatedCost" not in MODEL[MODEL.index("enum DisplayedSources"):MODEL.index("// MARK: - TokenDataModel")]
    assert "reset_entitlements" not in MODEL[MODEL.index("enum DisplayedSources"):MODEL.index("// MARK: - TokenDataModel")]


def test_readme_describes_v110_project_and_display_sources():
    assert "v1.1.1" in README
    assert "### About This Project" in README
    assert "### 关于本项目" in README
    assert "configurable display of both sources" in README
    assert "可选择同时显示两个来源" in README


def test_release_version_is_v111():
    build = (ROOT / "macos/build.sh").read_text(encoding="utf-8")
    cli = CLI
    assert 'VERSION="1.1.1"' in build
    assert 'CLI_VERSION = "1.1.1"' in cli


def test_settings_picker_is_not_two_toggles():
    start = VIEW.index("Displayed Sources")
    end = VIEW.index("Main Page Default Range", start)
    block = VIEW[start:end]
    assert "Picker" in block
    assert "Toggle" not in block
