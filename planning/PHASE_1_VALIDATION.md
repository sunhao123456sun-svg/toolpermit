# Phase 1 Validation Report

> Status: Passed
> Validation date: 2026-08-11
> Validated platforms: macOS 14 arm64 locally; Ubuntu 24.04 arm64 through Colima; GitHub-hosted Ubuntu, macOS, and Windows

## Chinese executive summary

Phase 1 的核心技术假设已在 macOS、Linux 和 Windows 实测通过：MCP `stdio` 透明代理、现代 2026 协议发现、旧版初始化兼容、Python 与 TypeScript 两个独立客户端、等待期间取消、审批摘要、SQLite 单次消费、重启恢复、脱敏落盘和静态 UI 资源打包均有可执行测试。

GitHub Actions 三系统矩阵在提交 `12e8f578fff43d02ec90f4cabb7912140c4a9dfd` 上全部成功，因此 Windows 托管门槛已满足，Phase 1 正式通过，可以进入 Phase 2。

## Environment

- Local Python: 3.12.13 in isolated `.venv`.
- Linux Python: 3.12.3 in an isolated Colima Ubuntu VM.
- MCP Python SDK: 2.0.0.
- MCP TypeScript SDK: 1.30.0.
- Node.js: 26 locally; CI target is Node 24.
- Test runner: pytest 8.4.2.

## Protocol discovery update

The MCP Python SDK 2.0.0 stable line implements the 2026-07-28 protocol while remaining compatible with earlier clients. The modern protocol uses `server/discover` and does not rely on the old connection handshake/session model. Planning references to a mandatory MCP session were therefore corrected to ToolPermit-owned run/connection correlation.

## Spike results

| Spike | Standard | Evidence | Result |
|---|---|---|---|
| S1 stdio mediation | Proxy initialize/discover, list, call, cancel, shutdown across target OSes | `test_stdio_proxy.py`; macOS, Linux, and Windows pass | Pass |
| S2 pause/resume and clients | Two independent clients; waiting call does not block cancellation | MCP Python 2.0 modern/legacy paths; TypeScript SDK 1.30; cancellation test | Pass |
| S3 canonical digest | Stable mapping; every security field bound; invalid numbers rejected | Hypothesis and golden tests in `test_canonical.py` | Pass |
| S4 SQLite lifecycle | Atomic single consumption and safe restart behavior | 32-worker race and recovery tests in `test_approval_store.py` | Pass across hosted matrix |
| S5 UI packaging | Static UI resources survive wheel build and clean install | Hatchling wheel installed in a fresh environment | Pass |
| S6 redaction/replay value | Secrets removed before SQLite; structure remains usable | `test_redaction.py` and canonical fixtures | Pass |

## Commands and results

### macOS

```text
.venv/bin/python -m pytest -q spikes/phase1/tests
15 passed

node spikes/phase1/node/client.mjs ...
typescript-client-ok
```

### Linux

```text
Colima Ubuntu 24.04 / Python 3.12
15 passed
```

### UI wheel

```text
Successfully built sdist and wheel
ui-wheel-asset-ok
```

## Findings

### F-01: Wire mediation is preferable to framework reimplementation

A line-oriented bidirectional proxy preserved both modern and legacy MCP flows without implementing an agent runtime. Production code should validate and mediate supported methods while transparently forwarding unrelated protocol messages.

### F-02: Client reading must continue while a call awaits approval

A sequential client-to-upstream loop would miss cancellation while `ask` is pending. Production mediation needs a per-call task/state model plus serialized upstream writes.

### F-03: MCP 2026 removes mandatory session assumptions

ToolPermit must own its `run_id` and `connection_id`. Protocol session identifiers are optional adapter metadata, not approval identity.

### F-04: Approval state can be consumed atomically in SQLite

A conditional `UPDATE ... WHERE state = 'approved'` allowed only one of 32 concurrent consumers to enter `executing`. In-flight rows must become `unknown` after recovery rather than being retried automatically.

### F-05: Static UI assets do not require a frontend build system

Framework-free HTML/CSS/JS can be included in a Python wheel and read through `importlib.resources`. This lowers v0.1 supply-chain and packaging complexity.

### F-06: Redaction reduces replay fidelity

Redaction-before-persistence works, but a replay cannot evaluate secret-dependent exact-value rules. The production event format needs an explicit redacted sentinel and replay diagnostics for unknown comparisons.

## Decisions resulting from Phase 1

- Target MCP Python SDK 2.x and test both modern discovery and legacy initialization compatibility.
- Use ToolPermit-owned run/connection correlation in approval digests.
- Keep a wire-level MCP adapter with strict supported-method parsing.
- Adopt a framework-free bundled local UI for v0.1 instead of React/Vite.
- Use SQLite conditional transitions and recover `executing` calls as `unknown`.
- Preserve redaction-before-persistence and make replay uncertainty explicit.

## Hosted matrix gate

Workflow: `.github/workflows/phase1-spikes.yml`

Passing run: [GitHub Actions run 31460643042](https://github.com/sunhao123456sun-svg/toolpermit/actions/runs/31460643042)

- Commit: `12e8f578fff43d02ec90f4cabb7912140c4a9dfd`.
- Ubuntu job: passed in 35 seconds.
- macOS job: passed in 39 seconds.
- Windows job: passed in 1 minute 14 seconds.

Required passing jobs:

- Ubuntu latest / Python 3.12.
- macOS latest / Python 3.12.
- Windows latest / Python 3.12.
- Python spike suite.
- TypeScript client integration.
- UI wheel asset verification.

## Architecture decision gate

The six required Phase 1 ADRs are written and accepted for v0.1 design:

- [ADR-001](adr/ADR-001-mcp-stdio-mediation.md): wire-level MCP stdio mediation.
- [ADR-002](adr/ADR-002-approval-canonicalization.md): versioned typed approval encoding and digest.
- [ADR-003](adr/ADR-003-policy-precedence.md): ordered first-match policy semantics.
- [ADR-004](adr/ADR-004-approval-transactions.md): SQLite conditional transitions and unknown recovery.
- [ADR-005](adr/ADR-005-local-ui.md): bundled framework-free local UI.
- [ADR-006](adr/ADR-006-audit-redaction.md): redaction-before-persistence and indeterminate replay.

## Exit decision

**Current decision: Phase 1 passed; enter Phase 2.**

All required hosted jobs and all six architecture decision records passed the gate. No Phase 1 exception or waiver is open.
