# QuotaView

QuotaView is a native macOS menu bar app for local, read-only monitoring of Antigravity and Codex usage.

It reads supported local client data and presents:

- identifiable input and output tokens;
- API-equivalent cost estimates (not an official bill);
- official-live quota status when the installed client exposes it;
- read-only Codex reset entitlements;
- today, the last 7 natural days, the last 30 natural days, and local all-time history;
- light, dark, and system appearance modes;
- the read-only `quotaview` CLI.

All data stays on the Mac. QuotaView does not upload account data, call remote telemetry services, write to official client endpoints, or reset, redeem, consume, or modify quota entitlements.

## Install

Download the macOS DMG or ZIP from the [Releases](../../releases) page. Move `QuotaView.app` to `/Applications` and launch it.

The release is unsigned or ad-hoc signed when no Developer ID certificate is available and is not notarized. macOS may require right-clicking the app and choosing **Open**, or allowing it under **Privacy & Security**.

The app requires a locally installed and signed-in Antigravity and/or Codex client for the corresponding data source.

### CLI

The app bundle contains the CLI. An optional shell installation is:

```bash
mkdir -p "$HOME/.local/bin"
ln -sf "/Applications/QuotaView.app/Contents/Resources/quotaview_cli.py" "$HOME/.local/bin/quotaview"
export PATH="$HOME/.local/bin:$PATH"
quotaview status --json
```

The CLI is read-only and uses the local Application Support data store.

## Privacy and limitations

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [PRIVACY_AUDIT.md](PRIVACY_AUDIT.md).

Known limitations:

- upstream local file formats, RPC methods, or client permissions may change;
- data that was deleted before the first scan cannot be reconstructed;
- local history is not the same as an official account-wide total;
- API-equivalent cost is an estimate based on configured reference rates, not an official invoice or account charge;
- hidden context, cloud-only work, and data not exposed by local clients may be missing;
- no Developer ID signature or notarization is included unless explicitly stated in the release.

No private screenshots are included. Add screenshots only after removing personal data and account information.

## Development

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

The build targets macOS 13 or newer and uses the host architecture. Release artifacts are produced locally and are intentionally not committed to Git.

## License

QuotaView is released under the MIT License. See [LICENSE](LICENSE).
