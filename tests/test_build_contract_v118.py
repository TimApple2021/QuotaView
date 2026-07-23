from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = (ROOT / "macos/build.sh").read_text(encoding="utf-8")


def test_build_targets_arm64_macos13():
    assert "-target arm64-apple-macos13.0" in BUILD


def test_build_signs_after_bundle_is_complete_and_before_install():
    plist_write = BUILD.index("CFBundleShortVersionString")
    sign = BUILD.index("codesign \\")
    install = BUILD.index('echo "=== 7. 安装 QuotaView 到 Applications ==="')
    assert plist_write < sign < install
    assert "--force" in BUILD[sign:install]
    assert "--deep" in BUILD[sign:install]
    assert "--sign -" in BUILD[sign:install]
    assert "--timestamp=none" in BUILD[sign:install]


def test_build_verifies_bundle_architecture_version_and_signature():
    sign = BUILD.index("codesign \\")
    install = BUILD.index('echo "=== 7. 安装 QuotaView 到 Applications ==="')
    contract = BUILD[sign:install]
    assert "--verify" in contract
    assert "--strict" in contract
    assert contract.index("--verify") > contract.index("--sign -")
    assert 'test "$ARCHS" = "arm64"' in contract
    assert 'test "$BUILT_VERSION" = "$VERSION"' in contract
    assert 'test "$BUILT_NUMBER" = "118"' in contract
    assert 'test "$BUILT_MINIMUM" = "13.0"' in contract


def test_build_does_not_start_app_or_read_runtime_data():
    forbidden = (
        "open -a",
        "launchctl",
        "quotaview_cli.py status",
        "Application Support",
        "cp -R data",
        "runtime_migration.py",
    )
    for value in forbidden:
        assert value not in BUILD
    assert "python3 monitor_backend.py" not in BUILD
    assert "python3 quotaview_cli.py" not in BUILD


def test_build_keeps_release_version():
    assert 'VERSION="1.1.8"' in BUILD
    assert '<string>118</string>' in BUILD
