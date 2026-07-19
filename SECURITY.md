# Security Policy

## Reporting

Please do not open a public issue containing credentials, tokens, cookies, logs, prompts, replies, account identifiers, or quota snapshots. Report suspected security issues privately through the repository's GitHub security contact or a private maintainer message.

Include a minimal reproduction, affected version, macOS version, and sanitized logs only. Never attach `auth.json`, Keychain exports, Application Support JSON, or raw client transcripts.

## Security model

QuotaView is intended to read local client data only. It does not upload data, use official write endpoints, or perform reset/redeem/consume actions. Users should review release signatures and Gatekeeper warnings before opening locally downloaded builds.
