# QuotaView

[English](README.md) | **简体中文**

QuotaView 是一款原生 macOS 菜单栏应用，用于本地、只读监控 Antigravity 和 Codex。当前最新版本为 **v1.1.1**。

## 功能

- 可识别的模型输入、模型输出和 Token 总量；
- API 等价成本估算（不是官方账单）；
- 官方客户端支持时显示 official-live 额度；
- 只读显示 Codex 使用限额重置权益；
- 今天、近 7 天、近 30 天、本地累计；
- 设置页可选择中文或 English；
- 浅色、深色和跟随系统主题；
- 只读 CLI：`quotaview`；
- 可选择同时显示两个来源，或仅显示 Antigravity / Codex。

QuotaView 将自身历史和设置保存在本机，不向开发者运营的服务器发送遥测或账户数据。官方客户端仍可能正常连接其自身服务。QuotaView 不写回官方客户端接口，也不执行额度 reset、redeem、consume 或修改操作。

Codex 套餐名称来自已安装官方客户端本地 `account/rateLimits/read` 响应中的 `rateLimitsByLimitId.codex.planType`。QuotaView 不根据额度百分比或用量猜测套餐。若官方响应缺少套餐字段，可显示带有较低置信度的本地 token 事件观察值；两者都没有时保持未知。

## 安装

从 [Releases](../../releases) 下载 DMG 或 ZIP，将 `QuotaView.app` 拖入“应用程序”后启动。当前版本支持 Apple Silicon（arm64），最低 macOS 13。

当前版本为 ad-hoc/linker 签名，未经过 Apple 公证。首次打开时，macOS 可能需要右键点击应用并选择“打开”，或在“系统设置 → 隐私与安全性”中允许。

## CLI

```bash
mkdir -p "$HOME/.local/bin"
ln -sf "/Applications/QuotaView.app/Contents/Resources/quotaview_cli.py" "$HOME/.local/bin/quotaview"
export PATH="$HOME/.local/bin:$PATH"
quotaview status --json
```

如果希望以后每次打开终端都能使用 `quotaview`，需要用户自行将 `~/.local/bin` 持久加入 shell 配置（例如 `~/.zshrc`）。

## 开发

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
./macos/build.sh
```

## 已知限制

应用依赖本机安装并登录官方客户端。上游本地格式或 RPC 方法可能发生变化。本地累计不等于官方账户累计，API 等价成本也不是官方账单。仓库不提交包含真实 Token、成本、额度、账户、套餐或重置时间的私人截图。

## 关于本项目

QuotaView 最初是根据我自己的本地监控需求开发的，目前作为个人开源项目维护。如果你在使用中遇到 Bug，或有实用的改进建议，欢迎通过 [GitHub Issues](../../issues) 反馈。

由于 Antigravity 和 Codex 属于上游产品，其本地数据格式或 RPC 接口发生变化时，可能影响部分功能的兼容性。

详见 [隐私政策](PRIVACY.md)、[安全说明](SECURITY.md)、[贡献指南](CONTRIBUTING.md) 和 [更新日志](CHANGELOG.md)。
