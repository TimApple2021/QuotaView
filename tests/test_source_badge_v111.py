from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
MODEL = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
CLI = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_both_mode_has_no_source_badge():
    assert "case .both: return nil" in VIEW
    assert "shouldShowSourceSegment" in VIEW


def test_antigravity_only_badge():
    assert 'case .antigravityOnly: return "Antigravity"' in VIEW
    assert 'selectedSource = .antigravity' in MODEL


def test_codex_only_badge():
    assert 'case .codexOnly: return "Codex"' in VIEW
    assert 'selectedSource = .codex' in MODEL


def test_badge_is_in_title_header():
    header = VIEW[VIEW.index("private var dashboardPage"):VIEW.index("if let err", VIEW.index("private var dashboardPage"))]
    assert "sourceBadgeLabel" in header
    assert "Text(sourceBadgeLabel)" in header


def test_badge_does_not_add_a_vertical_row():
    header = VIEW[VIEW.index("private var dashboardPage"):VIEW.index("Divider().background", VIEW.index("private var dashboardPage"))]
    assert header.count("HStack") == 1
    row = header[header.index("// Header Row"):header.index(".padding(.horizontal", header.index("// Header Row"))]
    assert "VStack" not in row


def test_badge_is_not_a_button():
    badge = VIEW[VIEW.index("if let sourceBadgeLabel"):VIEW.index("Spacer()", VIEW.index("if let sourceBadgeLabel"))]
    assert "Text(sourceBadgeLabel)" in badge
    assert "Button" not in badge


def test_badge_has_no_tap_gesture():
    badge = VIEW[VIEW.index("if let sourceBadgeLabel"):VIEW.index("Spacer()", VIEW.index("if let sourceBadgeLabel"))]
    assert "TapGesture" not in badge
    assert ".onTapGesture" not in badge


def test_light_badge_palette_exists():
    assert "sourceBadgeBackground = sourceBlue.opacity(light ? 0.10 : 0.18)" in VIEW
    assert "sourceBadgeBorder = sourceBlue.opacity(light ? 0.15 : 0.20)" in VIEW


def test_dark_badge_palette_exists():
    assert "light ? 0.10 : 0.18" in VIEW
    assert "light ? 0.15 : 0.20" in VIEW
    assert "sourceBadgeText = light ?" in VIEW


def test_badge_accessibility_labels_are_bilingual():
    assert "当前来源：\\(sourceBadgeLabel)" in VIEW
    assert "Current source: \\(sourceBadgeLabel)" in VIEW
    assert ".accessibilityAddTraits(.isStaticText)" in VIEW


def test_returning_to_both_hides_badge():
    block = VIEW[VIEW.index("private var sourceBadgeLabel"):VIEW.index("private var dashboardPage")]
    assert "case .both: return nil" in block


def test_single_source_segment_remains_hidden():
    assert "if dataModel.shouldShowSourceSegment" in VIEW
    assert "var shouldShowSourceSegment: Bool { displayedSources == .both }" in MODEL


def test_single_source_settings_persist_after_restart():
    assert 'UserDefaults.standard.set(displayedSources.rawValue, forKey: "displayedSources")' in MODEL
    assert 'ud.string(forKey: "displayedSources")' in MODEL
    assert "config.displayedSources" in MODEL


def test_restore_defaults_removes_badge_state():
    reset = VIEW[VIEW.index("private func resetDefaults"):VIEW.index("struct RefreshButtonIcon")]
    assert "dataModel.displayedSources = .both" in reset


def test_menu_bar_source_mapping_is_unchanged():
    assert "dashboard.sources[selectedSource.jsonKey]" in MODEL
    assert "updateMenuBarText()" in MODEL


def test_token_cost_quota_and_reset_code_is_not_in_badge_block():
    badge = VIEW[VIEW.index("private var sourceBadgeLabel"):VIEW.index("private var dashboardPage")]
    for forbidden in ("identifiableTokens", "estimatedCost", "reset_entitlements", "triggerScan"):
        assert forbidden not in badge


def test_cli_schema_remains_one():
    assert "SCHEMA_VERSION = 1" in CLI


def test_readme_and_changelog_are_v112():
    assert "v1.1.6" in README
    assert "About This Project" in README
    assert "## [1.1.6]" in CHANGELOG
    assert "compact source badge" in CHANGELOG
    assert "轻量来源标识" in CHANGELOG
