# QuotaView

**English** | [简体中文](README.zh-CN.md)

QuotaView is a native macOS menu bar app for local, read-only monitoring of Antigravity and Codex. The latest release is **v1.1.5**.

## Features

- identifiable input and output tokens;
- API-equivalent cost estimates (not an official bill);
- official-live quota status when supported by the installed client;
- read-only Codex reset entitlements;
- the reset badge and entitlement list are derived from the same normalized available set;
- today, last 7 natural days, last 30 natural days, and local all-time history;
- Chinese and English UI selectable in Settings;
- light, dark, and system appearance modes;
- the read-only `quotaview` CLI;
- configurable display of both sources, Antigravity only, or Codex only.

QuotaView stores its own history and settings locally and does not send telemetry or account data to a developer-operated server. Official clients may communicate with their own services normally. QuotaView does not write to official client endpoints, or reset, redeem, consume, or modify quota entitlements.

Installed builds store runtime data in `~/Library/Application Support/Antigravity Token Monitor/`; the project checkout is not required after installation.

Codex plan names are read from the installed official client's local `account/rateLimits/read` response, specifically `rateLimitsByLimitId.codex.planType`. QuotaView does not infer a plan from percentages or usage. If the official response has no plan type, a locally observed token event may be shown with a lower-confidence label; otherwise the plan remains unknown.

## Install

Download the macOS DMG or ZIP from [Releases](../../releases), move `QuotaView.app` to `/Applications`, and launch it. The current release is arm64 and requires macOS 13 or newer.

This release is ad-hoc/linker-signed and not notarized. macOS may require right-clicking the app and choosing **Open**, or allowing it under **Privacy & Security**.

## CLI

```bash
mkdir -p "$HOME/.local/bin"
ln -sf "/Applications/QuotaView.app/Contents/Resources/quotaview_cli.py" "$HOME/.local/bin/quotaview"
export PATH="$HOME/.local/bin:$PATH"
quotaview status --json
```

The `PATH` change must be persisted by the user in their shell configuration (for example, `~/.zshrc`) if the command should be available in future terminal sessions.

## Development

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

## Known Limitations

The app depends on locally installed and signed-in official clients. Upstream local formats or RPC methods may change. Local history is not an official account-wide total, and API-equivalent cost is not an official invoice. No private screenshots containing real tokens, costs, quotas, accounts, plans, or reset times are included.

## About This Project

QuotaView was originally created to meet my own local monitoring needs and is maintained as a personal open-source project. Bug reports and practical suggestions are welcome through [GitHub Issues](../../issues).

Because Antigravity and Codex are upstream products, changes to their local data formats or RPC interfaces may affect compatibility.

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [CHANGELOG.md](CHANGELOG.md).
