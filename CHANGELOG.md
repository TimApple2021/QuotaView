# Changelog

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
