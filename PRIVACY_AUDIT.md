# Privacy Audit

Release audit for QuotaView v1.0.0.

## Conclusion

The release candidate is designed for local-only, read-only monitoring. No network upload, telemetry, official write-back, entitlement reset, redeem, or consume operation is part of the application workflow.

## Repository cleanup

The release candidate excludes:

- runtime JSON and backup files;
- Application Support copies;
- conversation bodies and token/cost/quota history;
- official RPC raw responses and reset entitlement identifiers;
- credentials, cookies, authorization headers, Keychain data, and account identifiers;
- logs, screenshots, crash dumps, temporary apps, build directories, and audit scratch files;
- machine-specific absolute user paths in public source and documentation.

The scanner resolves the home directory at runtime. Documentation uses generic paths or `$HOME`.

## Verification scope

The final candidate is checked for credential-shaped strings, authorization headers, private account data, machine-specific paths, runtime artifacts, and large generated files. Findings are reported by type only; secret values and user data are not reproduced here.

Local runtime data is preserved on the user's Mac and is excluded from Git.
