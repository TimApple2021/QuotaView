# QuotaView

## English

QuotaView is a native macOS menu bar app for local, read-only monitoring of Antigravity and Codex. The latest release is **v1.1.0**.

Features:

- identifiable input and output tokens;
- API-equivalent cost estimates (not an official bill);
- official-live quota status when supported by the installed client;
- read-only Codex reset entitlements;
- today, last 7 natural days, last 30 natural days, and local all-time history;
- Chinese and English UI selectable in Settings;
- light, dark, and system appearance modes;
- the read-only `quotaview` CLI.
- configurable display of both sources, Antigravity only, or Codex only;

QuotaView stores its own history and settings locally and does not send telemetry or account data to a developer-operated server. Official clients may communicate with their own services normally. QuotaView does not write to official client endpoints, or reset, redeem, consume, or modify quota entitlements.

Codex plan names are read from the installed official client's local `account/rateLimits/read` response, specifically `rateLimitsByLimitId.codex.planType`. QuotaView does not infer a plan from percentages or usage. If the official response has no plan type, a locally observed token event may be shown with a lower-confidence label; otherwise the plan remains unknown.

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

The `PATH` change must be persisted by the user in their shell configuration (for example `~/.zshrc`) if the command should be available in future terminal sessions.

### Development

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

Known limitations: the app depends on locally installed and signed-in official clients; upstream local formats/RPC methods may change; local history is not an official account-wide total; API-equivalent cost is not an official invoice. No private screenshots are included.

### About This Project

QuotaView was originally created to meet my own local monitoring needs and is maintained as a personal open-source project. Bug reports and practical suggestions are welcome through [GitHub Issues](../../issues).

Because Antigravity and Codex are upstream products, changes to their local data formats or RPC interfaces may affect compatibility.

See [PRIVACY.md](PRIVACY.md), [SECURITY.md](SECURITY.md), and [CONTRIBUTING.md](CONTRIBUTING.md).

## 中文

QuotaView 是一款原生 macOS 菜单栏应用，用于本地、只读监控 Antigravity 和 Codex。当前最新版本为 **v1.1.0**。

功能包括：

- 可识别的模型输入、模型输出和 Token 总量；
- API 等价成本估算（不是官方账单）；
- 官方客户端支持时显示 official-live 额度；
- 只读显示 Codex 使用限额重置权益；
- 今天、近 7 天、近 30 天、本地累计；
- 设置页可选择中文或 English；
- 浅色、深色和跟随系统主题；
- 只读 CLI：`quotaview`。
- 可选择同时显示两个来源，或仅显示 Antigravity / Codex；

QuotaView 将自身历史和设置保存在本机，不向开发者运营的服务器发送遥测或账户数据。官方客户端仍可能正常连接其自身服务。QuotaView 不写回官方客户端接口，也不执行额度 reset、redeem、consume 或修改操作。

Codex 套餐名称来自已安装官方客户端本地 `account/rateLimits/read` 响应中的 `rateLimitsByLimitId.codex.planType`。QuotaView 不根据额度百分比或用量猜测套餐。若官方响应缺少套餐字段，可显示带有较低置信度的本地 token 事件观察值；两者都没有时保持未知。

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

如果希望以后每次打开终端都能使用 `quotaview`，需要用户自行将 `~/.local/bin` 持久加入 shell 配置（例如 `~/.zshrc`）。

### 开发与限制

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

已知限制：依赖本机安装并登录官方客户端；上游本地格式或 RPC 方法变化可能导致读取失效；本地累计不等于官方账户累计；API 等价成本不是官方账单。仓库不提交包含私人数据的截图。

### 关于本项目

QuotaView 最初是根据我自己的本地监控需求开发的，目前作为个人开源项目维护。如果你在使用中遇到 Bug，或有实用的改进建议，欢迎通过 [GitHub Issues](../../issues) 反馈。

由于 Antigravity 和 Codex 属于上游产品，其本地数据格式或 RPC 接口发生变化时，可能影响部分功能的兼容性。

详见 [隐私政策](PRIVACY.md)、[安全说明](SECURITY.md) 和 [贡献指南](CONTRIBUTING.md)。
