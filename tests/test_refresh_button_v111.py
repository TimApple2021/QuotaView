from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
MODEL = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")
CLI = (ROOT / "cli/quotaview_cli.py").read_text(encoding="utf-8")


def refresh_block():
    return VIEW[VIEW.index("struct RefreshButtonStyle"):VIEW.index("struct RefreshButtonIcon")]


def icon_block():
    return VIEW[VIEW.index("struct RefreshButtonIcon"):]


def test_refresh_button_has_transparent_click_target_only():
    assert "struct RefreshButtonStyle" in VIEW
    assert "Circle()" not in refresh_block()
    assert ".background" not in refresh_block()
    assert ".overlay" not in refresh_block()


def test_refresh_button_uses_double_arrow_cycle_symbol():
    assert 'Image(systemName: "arrow.triangle.2.circlepath")' in icon_block()
    assert 'Image(systemName: "arrow.clockwise")' not in VIEW
    assert "arrow.clockwise.circle" not in VIEW


def test_refresh_button_is_32_by_32():
    assert ".frame(width: 32, height: 32" in VIEW


def test_refresh_icon_uses_existing_footer_icon_color():
    assert "refreshButtonIcon = Color(nsColor: .secondaryLabelColor)" in VIEW


def test_no_refresh_background_or_shadow_style_exists():
    for forbidden in ("refreshButtonBackground", "refreshButtonHoverBackground", "refreshButtonPressedBackground", "refreshButtonBorder", "refreshButtonShadow", ".shadow"):
        assert forbidden not in refresh_block()


def test_only_image_rotates():
    assert ".rotationEffect(.degrees(angle), anchor: .center)" in icon_block()
    assert ".rotationEffect" not in refresh_block()
    assert "Circle()" not in refresh_block()
    assert "Circle()" not in icon_block()


def test_scan_rotation_still_resets_to_zero():
    assert ": 0.0" in icon_block()
    assert "refreshAnimationStart = nil" in icon_block()


def test_scanning_disables_repeat_trigger():
    assert ".disabled(dataModel.isScanning)" in VIEW
    assert "dataModel.triggerScan()" in VIEW


def test_existing_scan_lock_remains_unchanged():
    backend = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
    assert "fcntl.flock" in backend
    assert "scan.lock" in backend


def test_refresh_button_keeps_left_footer_and_settings_button():
    footer = VIEW[VIEW.index("// Footer"):VIEW.index("private var settingsPage")]
    assert "dataModel.triggerScan()" in footer
    assert 'Image(systemName: "gearshape")' in footer
    assert ".frame(width: 32, height: 32" in footer


def test_settings_gear_is_visually_balanced_without_changing_refresh():
    footer = VIEW[VIEW.index("// Footer"):VIEW.index("private var settingsPage")]
    assert '.font(.system(size: 20, weight: .medium))' in footer
    assert '.frame(width: 32, height: 32, alignment: .center)' in footer
    assert 'Image(systemName: "arrow.triangle.2.circlepath")' in VIEW
    assert '.font(.system(size: 18, weight: .medium))' in icon_block()
    assert '.frame(width: 32, height: 28' not in footer


def test_settings_button_was_not_replaced_by_refresh_style():
    settings = VIEW[VIEW.index('Image(systemName: "gearshape")'):VIEW.index("private func modelPriceRow")]
    assert "RefreshButtonStyle" not in settings


def test_accessibility_labels_are_bilingual():
    assert '"正在刷新数据"' in VIEW
    assert '"Refreshing Data"' in VIEW
    assert '"刷新数据"' in VIEW
    assert '"Refresh Data"' in VIEW


def test_refresh_button_is_a_button_for_voiceover():
    footer = VIEW[VIEW.index("// Footer"):VIEW.index("private var settingsPage")]
    assert "Button { dataModel.triggerScan() }" in footer
    assert ".accessibilityLabel(dataModel.isScanning" in footer


def test_token_cost_quota_reset_and_cli_contracts_are_not_in_button_style():
    block = refresh_block()
    for forbidden in ("identifiableTokens", "estimatedCost", "reset_entitlements", "scan_codex", "SCHEMA_VERSION"):
        assert forbidden not in block
    assert "SCHEMA_VERSION = 1" in CLI


def test_no_refresh_logic_added_to_backend():
    backend = (ROOT / "monitor_backend.py").read_text(encoding="utf-8")
    assert "def scan_conversations" in backend
    assert "def scan_codex_conversations" in backend
    assert "RefreshButtonStyle" not in backend
