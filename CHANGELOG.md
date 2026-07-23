# Changelog

## v1.1.8

### Added

- DeepSeek as a third independent data source.
- Official DeepSeek balance refresh.
- Direct import of DeepSeek usage ZIP exports.
- UTC monthly filtering and monthly summaries.
- Model and historical API-key usage breakdowns.
- DeepSeek CLI `status` and `import` support.
- A separate DeepSeek settings page.

### Improved

- Stable identity merging when the same API key is renamed.
- Idempotent duplicate and overlapping ZIP imports.
- Independent Antigravity, Codex, and DeepSeek menu-bar totals.
- A unified Dashboard shell for the DeepSeek page.
- English localization and pricing layout.
- Historical model ID parsing off the SwiftUI main thread.
- Atomic Codex scan-cache writes and backup recovery.
- Stable settings menus and complete source labels.

### Security / Privacy

- DeepSeek API keys remain in a local private credential file.
- Application Support data uses a private directory and credential files use restrictive permissions.
- Credentials, billing data, ZIP exports, and runtime data are excluded from Git, App Resources, and release packages.
- Builds do not read or modify Application Support runtime data.

## [1.1.7] - 2026-07-22

- Moved historical model ID parsing off the Swift main thread using a background utility queue; a generation counter prevents stale results from overwriting a newer refresh.
- Added atomic writes, fsync, and `.bak` backup recovery for the Codex scan cache; a corrupt cache no longer affects the primary token ledger.
- Unified menu-bar accumulated-cost formatting: both Antigravity and Codex now display `$X.XX` (removed the `C` suffix for Codex).
- Replaced all six `.pickerStyle(.menu)` settings pickers with `StableSettingsMenu`, a reusable `Menu`-based control that opens from a fixed anchor and avoids the system-repositioning behaviour near the top of the screen.
- Removed the automatic invocation of `runtime_migration.py` from `macos/build.sh`; the migration utility now requires an explicit `--source` and `--target` and prints a warning when the project `data/` directory is used as a source.
- App Resources no longer include `runtime_migration.py` or any runtime JSON files.
- Regression tests for all of the above changes.
- No changes to CLI schema, token totals, quota calculations, model pricing, or reset entitlement behaviour.

### v1.1.7（中文）

- 将历史模型 ID 解析移至 Swift Utility 后台队列；使用 generation 计数器防止旧的异步结果覆盖新刷新结果。
- 为 Codex 扫描缓存添加原子写入、fsync 和 `.bak` 备份恢复；缓存损坏不再影响主账本。
- 统一菜单栏"累计费用"格式：Antigravity 和 Codex 均显示 `$X.XX`（删除 Codex 的 `C` 后缀）。
- 将设置页六个 `.pickerStyle(.menu)` 选择器替换为可复用的 `StableSettingsMenu`，从固定锚点弹出菜单，避免在屏幕顶部附近时系统重新定位。
- 从 `macos/build.sh` 删除 `runtime_migration.py` 的自动调用；迁移工具现在要求显式提供 `--source` 和 `--target`，使用项目 `data/` 目录时给出警告。
- App Resources 不再包含 `runtime_migration.py` 或运行时 JSON 文件。
- 以上变更的回归测试。
- 不改变 CLI schema、Token 总量、额度计算、模型价格或重置权益行为。

## [1.1.6] - 2026-07-22

- Added official Gemini 3.6 Flash pricing support.
- Normalized Gemini 3.5 and 3.6 Flash Low, Medium, and High reasoning levels into one canonical model entry per model.
- Added evidence-based conditional mapping for Antigravity's internal `gemini-3-flash-c` identifier when it corresponds to Gemini 3.5 Flash.
- Prevented unknown runtime model identifiers from automatically appearing as editable official pricing entries.
- Preserved raw model identifiers and historical token totals for diagnostics and traceability.
- Expanded CLI doctor diagnostics and regression coverage.
- No changes to the CLI schema, token totals, quota calculations, or reset entitlement behavior.

### v1.1.6（中文）

- 增加 Gemini 3.6 Flash 正式价格支持。
- 将 Gemini 3.5 和 3.6 Flash 的 Low、Medium、High 思考等级分别归一为一个 canonical 模型项。
- 增加基于证据的 `gemini-3-flash-c` 条件映射；仅在对应 Gemini 3.5 Flash 时映射。
- 防止未知运行时模型 ID 自动进入可编辑的正式价格目录。
- 保留原始模型 ID 和历史 Token 总量，用于诊断和追溯。
- 扩展 CLI doctor 诊断和回归测试覆盖。
- 不改变 CLI schema、Token 总量、额度计算或重置权益行为。

## [1.1.5] - 2026-07-20

- Fixed an inconsistency where the reset badge could show an available reset while the entitlement list appeared empty.
- Unified reset availability normalization across the backend, CLI, and Swift UI.
- Added support for additional entitlement status and expiration formats.
- Preserved reset counts and entitlement details together as an atomic stale snapshot.
- Added non-sensitive reset consistency diagnostics to the CLI.
- No reset, redeem, or consume actions were added.

### v1.1.5（中文）

- 修复重置徽标显示可用次数，但下方权益列表为空的不一致问题。
- 统一后端、CLI 和 Swift UI 的重置权益可用状态规范化逻辑。
- 增加对更多状态值和到期时间格式的兼容。
- stale 状态下将数量与权益详情作为同一个原子快照保留。
- CLI 增加不含敏感信息的一致性诊断字段。
- 未增加任何重置、兑换或消耗操作。

## [1.1.4] - 2026-07-20

- Preserved the last successful quota and reset entitlement data when an official RPC refresh fails temporarily.
- Added `official_stale` status with last-success and last-attempt metadata.
- Added limited retries for transient transport failures.
- Prevented failed token scans from replacing existing usage data with zeros.
- Added dashboard backup recovery and additional refresh sequencing safeguards.
- No changes to token pricing, quota calculations, local history, or CLI schema.

### v1.1.4（中文）

- 官方 RPC 瞬时刷新失败时，保留上一次成功的额度和重置权益数据。
- 增加 `official_stale` 状态及最近成功、最近尝试时间信息。
- 为瞬时传输错误增加有限重试。
- 防止 Token 扫描失败时用零覆盖已有使用数据。
- 增加 dashboard 备份恢复和刷新顺序保护。
- 不涉及 Token 定价、额度计算、本地历史或 CLI schema 变更。

## [1.1.3] - 2026-07-20

- Migrated runtime data to the canonical macOS Application Support directory.
- Removed production dependencies on the development project directory.
- Added safe one-time runtime data migration and atomic persistence.
- Prevented executable app bundles from being stored in backup directories.
- Fixed a condition that could allow an old backup build to relaunch at login.

### v1.1.3（中文）

- 将运行数据迁移到规范的 macOS Application Support 目录。
- 移除正式版本对开发项目目录的依赖。
- 增加安全的一次性数据迁移与原子写入。
- 禁止在备份目录中保留可执行 App Bundle。
- 修复旧备份版本可能在登录时重新启动的问题。

## [1.1.2] - 2026-07-20

- Replaced the refresh icon with a double-arrow cycle symbol.
- Matched the settings gear’s visual size to the refresh icon.
- Kept both bottom toolbar controls background-free and visually balanced.
- No changes to monitoring, quota, pricing, history, or CLI schema.

### v1.1.2（中文）

- 将刷新图标替换为双箭头循环样式。
- 调整设置齿轮的视觉尺寸，使其与刷新图标保持对称。
- 两个底栏按钮继续保持无背景、无边框的简洁样式。
- 不涉及统计、额度、价格、历史或 CLI schema 变更。

## [1.1.1] - 2026-07-19

- Added a compact source badge to the title bar in single-source mode.
- The badge identifies Antigravity or Codex without restoring the source switcher.
- No changes to monitoring, quota, pricing, history, or CLI behavior.

### v1.1.1（中文）

- 单来源模式在标题栏增加轻量来源标识。
- 在不恢复来源切换器的情况下明确显示 Antigravity 或 Codex。
- 不涉及统计、额度、价格、历史或 CLI 行为变更。

## [1.1.0] - 2026-07-19

- Added a mutually exclusive Displayed Sources setting for both sources, Antigravity only, or Codex only.
- Added bilingual About This Project documentation.
- Kept scanning, token accounting, costs, quotas, prices, reset entitlements, and CLI schema unchanged.

## [1.0.2] - 2026-07-19

- Read Codex plan type from the official local `account/rateLimits/read` response.
- Use a local observed plan only as an explicitly labelled fallback; never guess Plus.
- Localize Codex plan titles, reset names, dates, and error labels in English and Chinese.
- Keep CLI schema version 1 while exposing non-sensitive plan metadata.

## [1.0.1] - 2026-07-19

- Added Chinese / English language selection in Settings.
- Localized the main dashboard, quota cards, reset entitlement section, settings labels, range labels, and pricing explanations.
- Added bilingual README documentation.

## [1.0.0] - 2026-07-19

- Initial QuotaView release.
- Native macOS menu bar UI for Antigravity and Codex.
- Local token, API-equivalent cost, official-live quota, and read-only reset entitlement views.
- Natural-day ranges: today, 7 days, 30 days, and local all-time.
- Read-only `quotaview` CLI.
- Light, dark, and system appearance support.
