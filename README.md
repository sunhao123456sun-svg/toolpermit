# ToolPermit

[![CI](https://github.com/sunhao123456sun-svg/toolpermit/actions/workflows/ci.yml/badge.svg)](https://github.com/sunhao123456sun-svg/toolpermit/actions/workflows/ci.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11%E2%80%933.13-28527a)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-6b4fbb)](LICENSE)

ToolPermit is a local-first permission policy, one-time approval, and redacted audit layer for
[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) tool calls. Put it between a
local MCP client and a `stdio` server to observe calls, enforce explainable `allow / ask / deny`
rules, review exceptional actions, and replay recorded calls against a candidate policy.

> Current release: [v0.1.0 on PyPI](https://pypi.org/project/toolpermit/0.1.0/), with a matching
> [GitHub Release](https://github.com/sunhao123456sun-svg/toolpermit/releases/tag/v0.1.0).

English is authoritative for project contracts. See [README.zh-CN.md](README.zh-CN.md) for the
Chinese feature overview and quickstart.

## Why ToolPermit?

- **Deterministic policy:** strict, versioned YAML; first match wins and every result explains why.
- **Exact one-time approval:** an approval is bound to the canonical request, policy, session, and
  expiry, then consumed atomically.
- **Redaction before storage:** recognized secrets and sensitive keys are irreversibly replaced
  before SQLite persistence, display, or JSONL export.
- **Offline replay:** compare policies against stored, redacted calls without starting the MCP
  server or executing a tool.
- **Local interfaces:** every core workflow is available from the CLI; the optional approval UI is
  restricted to loopback and protected by Host, Origin, CSRF, CSP, and SameSite controls.
- **Portable core:** tested on Ubuntu, macOS, and Windows with Python 3.11, 3.12, and 3.13.

![ToolPermit loopback approval UI with fictional contained-demo data](docs/assets/toolpermit-ui.jpg)

## Codex Skill

Install the ToolPermit Codex Skill from this GitHub repository with the built-in plugin manager:

```bash
codex plugin marketplace add sunhao123456sun-svg/toolpermit --ref main
codex plugin add toolpermit@toolpermit
```

Start a new task, then ask:

```text
Use $toolpermit to install ToolPermit and safely wrap my local MCP stdio server in observe mode.
```

The Skill checks the environment, installs the compatible Python package when authorized, preserves
existing files, shows MCP client changes before writing them, and keeps enforcement and exact
approvals user-controlled. See the [Codex Skill installation and usage guide](docs/codex-skill.md)
for updating, removal, trigger examples, and limitations.

## Ten-minute quickstart

Requirements: Python 3.11–3.13. A local checkout is also needed for the contained demo scripts.

```bash
python -m venv .venv
.venv/bin/python -m pip install "toolpermit==0.1.0"
.venv/bin/toolpermit init
```

On Windows PowerShell, use `.venv\Scripts\python` and `.venv\Scripts\toolpermit`.

Observe the contained demo. The only write target is the disposable directory you provide:

```bash
mkdir demo-workspace
.venv/bin/python examples/demo_client.py \
  --mode observe \
  --demo-dir demo-workspace
.venv/bin/toolpermit runs list
```

To see a one-time approval, start the same client in enforce mode. It waits before the demo file
is written:

```bash
.venv/bin/python examples/demo_client.py \
  --mode enforce \
  --policy toolpermit.yaml \
  --demo-dir demo-workspace
```

In a second terminal, approve from the CLI:

```bash
.venv/bin/toolpermit approvals list
.venv/bin/toolpermit approvals approve APPROVAL_ID
```

Or launch the loopback UI with `.venv/bin/toolpermit ui`. Continue with the
[complete quickstart](docs/quickstart.md), including policy suggestion, replay, and cleanup.

## Policy example

```yaml
version: 1
default: deny
rules:
  - id: allow-demo-read
    action: allow
    explanation: Reading from the contained demo is expected.
    match:
      tool: read_demo
  - id: review-demo-write
    action: ask
    explanation: Demo writes require one-time local approval.
    match:
      tool: write_demo
```

Unknown keys and invalid rules fail validation. See the [policy reference](docs/policy-reference.md)
for matching, precedence, canonicalization, redaction uncertainty, and examples.

## Supported scope

v0.1 supports one local user, MCP over `stdio`, YAML policy version 1, SQLite audit schema version
1, CLI approval, and a loopback-only web UI. It does **not** provide an operating-system sandbox,
authenticate remote users, inspect calls that bypass the proxy, undo an executed tool action, or
guarantee that a permitted path is safe from every symlink/TOCTOU race.

Read [Security](docs/security.md), [Privacy and data lifecycle](docs/privacy.md), and
[Known limitations](docs/limitations.md) before using enforcement around destructive tools.

## Documentation

- [Quickstart](docs/quickstart.md)
- [Codex Skill](docs/codex-skill.md)
- [CLI reference](docs/cli-reference.md)
- [Configuration](docs/configuration.md)
- [Policy reference](docs/policy-reference.md)
- [Architecture](docs/architecture.md)
- [Security model](docs/security.md)
- [Privacy, retention, export, and deletion](docs/privacy.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Known limitations](docs/limitations.md)
- [Policy benchmark](benchmarks/README.md)
- [Contributing](CONTRIBUTING.md) and [support](SUPPORT.md)

## Development

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/ruff check src tests examples scripts benchmarks plugins
.venv/bin/pyright
.venv/bin/python scripts/check_codex_plugin.py
.venv/bin/pytest --cov=toolpermit --cov-fail-under=70
```

The release process, compatibility policy, and stage evidence are documented in
[docs/releasing.md](docs/releasing.md) and [planning/](planning/).

## License

Licensed under the [Apache License 2.0](LICENSE).
