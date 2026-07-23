"""Source-level contracts for stable Menu-based settings selectors.

The final accepted design is a plain-text label with no arrow indicator of
any kind (no MenuChevronDown, no system chevron, no overlay image).
"""

from pathlib import Path


ROOT = Path(__file__).parent.parent
VIEW = (ROOT / "macos/AntigravityTokenMonitor/MenuBarView.swift").read_text(encoding="utf-8")
MODEL = (ROOT / "macos/AntigravityTokenMonitor/TokenDataModel.swift").read_text(encoding="utf-8")


def settings_block():
    start = VIEW.index("private var settingsPage")
    return VIEW[start:]


def test_reusable_menu_component_is_anchor_based_and_has_checkmark():
    component = VIEW[VIEW.index("struct StableSettingsMenu"):VIEW.index("// MARK: - MenuBarView")]
    assert "Menu {" in component
    assert "Button {" in component
    assert "selection = option" in component
    assert 'Image(systemName: "checkmark")' in component
    assert ".menuStyle(.borderlessButton)" in component
    assert ".menuIndicator(.hidden)" in component
    assert ".contentShape(Rectangle())" in component


def test_label_is_plain_text_no_arrow_of_any_kind():
    # The entire MenuBarView source must not contain any arrow/chevron artifact.
    assert "MenuChevronDown" not in VIEW
    assert 'Image(systemName: "chevron.down")' not in VIEW
    assert 'Image(systemName: "chevron.up.chevron.down")' not in VIEW
    assert "allowsHitTesting(false)" not in VIEW


def test_menu_label_is_text_only():
    component = VIEW[VIEW.index("struct StableSettingsMenu"):VIEW.index("// MARK: - MenuBarView")]
    label_start = component.index('} label: {')
    indicator_start = component.index(".menuIndicator(.hidden)")
    menu_label = component[label_start:indicator_start]
    assert "Text(title(selection))" in menu_label
    assert "MenuChevronDown" not in menu_label
    assert 'Image(systemName: "chevron.down")' not in menu_label
    assert "Label(" not in menu_label
    assert ".contentShape(Rectangle())" in menu_label
    assert ".frame(width: width, height: 28" in menu_label


def test_menu_hit_area_covers_control_width():
    component = VIEW[VIEW.index("struct StableSettingsMenu"):VIEW.index("// MARK: - MenuBarView")]
    label_start = component.index('} label: {')
    menu_label = component[label_start:component.index(".menuIndicator(.hidden)")]
    assert ".frame(width: width, height: 28" in menu_label
    assert ".contentShape(Rectangle())" in menu_label
    assert ".onTapGesture" not in component
    assert ".allowsHitTesting(false)" not in component


def test_settings_selectors_no_longer_use_menu_picker_style():
    assert ".pickerStyle(.menu)" not in settings_block()
    assert settings_block().count("StableSettingsMenu(") == 6


def test_menu_bar_display_options_keep_order_and_labels():
    block = settings_block()
    assert "options: Array(MenuBarDisplay.allCases)" in block
    for value in (".iconOnly", ".todayTotal", ".days7Total", ".days30Total", ".allTotal", ".allCost"):
        assert value in MODEL


def test_all_settings_option_collections_remain_complete():
    block = settings_block()
    assert "Array(DisplayedSources.allCases)" in block
    assert "Array(TimeRange.allCases)" in block
    assert "Array(RefreshInterval.allCases)" in block
    assert "Array(AppTheme.allCases)" in block
    assert "options: [.chinese, .english]" in block


def test_widths_are_content_specific_and_source_is_wide_enough():
    assert "width: 160" in VIEW
    assert "width: 205" in VIEW
    assert "width: 145" in VIEW
    assert "width: 128" in VIEW
    assert "width: 138" in VIEW
    assert "width: 110" in VIEW
    assert "全部" in MODEL
    assert "All" in MODEL



def test_existing_persistence_and_side_effect_bindings_are_unchanged():
    for key in ("menuBarDisplay", "displayedSources", "selectedRange", "refreshInterval", "theme", "language"):
        assert key in MODEL
    assert "updateMenuBarText()" in MODEL
    assert "setupTimer()" in MODEL
    assert "persistSettingsIfReady()" in MODEL
