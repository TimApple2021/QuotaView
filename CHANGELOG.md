# Changelog

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
