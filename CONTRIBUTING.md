# Contributing

Thank you for helping improve QuotaView.

Before opening a change:

1. Keep runtime data, logs, screenshots, backups, and private transcripts out of Git.
2. Do not add credentials, cookies, authorization headers, account identifiers, or raw official responses.
3. Preserve the read-only behavior for provider data and reset entitlements.
4. Run the Python tests and Swift type check locally.

```bash
python3 -m pytest tests/ -v
swiftc -typecheck macos/AntigravityTokenMonitor/*.swift
```

Keep changes focused and document compatibility impacts for local client formats, pricing, quota readers, or the CLI schema.
