# Changelog

All notable changes are documented here. The format follows Keep a Changelog, and versions follow
Semantic Versioning while the project remains pre-1.0.

## [Unreleased]

### Added

- Installable ToolPermit Codex Skill and skills-only Plugin with a Git marketplace, observe-first
  workflow, read-only environment doctor, and repo-local discovery.

### Changed

- Installation documentation now points to the published PyPI and GitHub v0.1.0 artifacts.

## [0.1.0] - 2026-08-11

### Added

- MCP `stdio` proxy with observe and enforce modes.
- Strict YAML policy schema with deterministic first-match evaluation.
- Race-safe one-time approvals with expiry, rejection, cancellation, and restart recovery.
- Redaction-before-storage SQLite audit trail and deterministic JSONL export.
- Offline policy replay and inactive policy candidate generation.
- Complete CLI and protected loopback approval/run-inspection UI.
- Cross-platform tests for Ubuntu, macOS, Windows, and Python 3.11–3.13.

### Security

- Approval digests bind the request, tool schema, session, policy, and expiry.
- Browser endpoints enforce exact Host and Origin checks, per-session CSRF tokens, restrictive CSP,
  SameSite cookies, and no permissive CORS.

### Fixed

- Proxy shutdown now gives an EOF-aware upstream server a bounded graceful-exit window before
  termination, removing a cross-platform exit-code race after pre-execution cancellation.

[Unreleased]: https://github.com/sunhao123456sun-svg/toolpermit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sunhao123456sun-svg/toolpermit/releases/tag/v0.1.0
