# QuotaView

## English

QuotaView is a native macOS menu bar app for local, read-only monitoring of Antigravity and Codex.

Features:

- identifiable input and output tokens;
- API-equivalent cost estimates (not an official bill);
- official-live quota status when supported by the installed client;
- read-only Codex reset entitlements;
- today, last 7 natural days, last 30 natural days, and local all-time history;
- Chinese and English UI selectable in Settings;
- light, dark, and system appearance modes;
- the read-only `quotaview` CLI.

All data stays on the Mac. QuotaView does not upload account data, send telemetry, write to official client endpoints, or reset, redeem, consume, or modify quota entitlements.

### Install

Download the macOS DMG or ZIP from [Releases](../../releases), move `QuotaView.app` to `/Applications`, and launch it. The current release is arm64 and requires macOS 13 or newer.

This release is ad-hoc/linker-signed and not notarized. macOS may require right-clicking the app and choosing **Open**, or allowing it under **Privacy & Security**.

### CLI

```bash
mkdir -p "$HOME/.local/bin"
ln -sf "/Applications/QuotaView.app/Contents/Resources/quotaview_cli.py" "$HOME/.local/bin/quotaview"
export PATH="$HOME/.local/bin:$PATH"
quotaview status --json
```

### Development

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

Known limitations: the app depends on locally installed and signed-in official clients; upstream local formats/RPC methods may change; local history is not an official account-wide total; API-equivalent cost is not an official invoice. No private screenshots are included.

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

## 中文

QuotaView 是一款原生 macOS 菜单栏应用，用于本地、只读监控 Antigravity 和 Codex。

功能包括：

- 可识别的模型输入、模型输出和 Token 总量；
- API 等价成本估算（不是官方账单）；
- 官方客户端支持时显示 official-live 额度；
- 只读显示 Codex 使用限额重置权益；
- 今天、近 7 天、近 30 天、本地累计；
- 设置页可选择中文或 English；
- 浅色、深色和跟随系统主题；
- 只读 CLI：`quotaview`。

所有数据都保存在本机。QuotaView 不上传账户数据、不发送遥测、不写回官方客户端接口，也不执行额度 reset、redeem、consume 或修改操作。

### 安装

从 [Releases](../../releases) 下载 DMG 或 ZIP，将 `QuotaView.app` 拖入“应用程序”后启动。当前版本支持 Apple Silicon（arm64），最低 macOS 13。

当前版本为 ad-hoc/linker 签名，未经过 Apple 公证。首次打开时，macOS 可能需要右键点击应用并选择“打开”，或在“系统设置 → 隐私与安全性”中允许。

### CLI 安装

```bash
mkdir -p "$HOME/.local/bin"
ln -sf "/Applications/QuotaView.app/Contents/Resources/quotaview_cli.py" "$HOME/.local/bin/quotaview"
export PATH="$HOME/.local/bin:$PATH"
quotaview status --json
```

### 开发与限制

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

已知限制：依赖本机安装并登录官方客户端；上游本地格式或 RPC 方法变化可能导致读取失效；本地累计不等于官方账户累计；API 等价成本不是官方账单。仓库不提交包含私人数据的截图。

详见 [隐私政策](PRIVACY.md)、[安全说明](SECURITY.md) 和 [贡献指南](CONTRIBUTING.md)。
