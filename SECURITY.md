# Security policy

## Supported versions

Security fixes are released for the latest minor version.

| Version | Supported |
|---|---|
| 1.0.x | yes |

## Reporting a vulnerability

Please **do not** open a public issue. Report privately through GitHub: **Security → Report a vulnerability** on this repository. Include steps to reproduce, the affected file or command, and the impact you expect.

You will get an acknowledgement within five working days and a status update at least every two weeks until the issue is resolved.

## Scope and design notes

- API keys are read from environment variables only. Profiles store variable *names*; keys are never written to sidecars, logs or prompts, and `--dry-run` masks them.
- Provider responses, downloaded files and leaderboard pages are treated as data, never as instructions.
- Downloads follow only URLs returned by the configured provider; authentication is attached to downloads only when a profile sets `download_with_auth`.
