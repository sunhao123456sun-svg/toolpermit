# Contributing

Thank you for improving ToolPermit. Security and data-integrity behavior needs evidence, not only a
happy-path demonstration.

## Before opening a change

Use a GitHub issue for substantial features or security-boundary changes. Use private vulnerability
reporting for suspected vulnerabilities. Small fixes, tests, and documentation corrections can go
directly to a pull request.

## Local setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/ruff check src tests examples scripts benchmarks
.venv/bin/pyright
.venv/bin/pytest --cov=toolpermit --cov-fail-under=70
```

Windows contributors can use the corresponding `.venv\Scripts\` commands.

## Change expectations

- Add tests for behavior and failure modes. Approval, policy, redaction, and proxy changes require a
  negative test proving the unsafe path does not execute.
- Keep policy evaluation deterministic and free of database, network, subprocess, clock, and UI
  dependencies.
- Update English authoritative documentation and the Chinese README when commands or advertised
  features change.
- Do not add telemetry or send audit data off-device.
- Do not commit credentials, real personal data, generated databases, build artifacts, or virtual
  environments.
- Explain compatibility, migration, and threat-model consequences in the pull request.

## Pull requests

Use a short-lived branch and a focused Conventional Commit-style title such as `fix: reject stale
approval digest`. CI must pass on every supported operating system and Python version. Maintainers
may request a smaller change if review would otherwise mix unrelated security decisions.

By submitting a contribution, you agree that it is licensed under Apache-2.0 and that you have the
right to submit it. Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
