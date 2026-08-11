# Product Requirements Document

> Product: ToolPermit  
> Release target: v0.1.0  
> Status: Draft; no implementation is authorized by this document alone.

## Chinese executive summary

v0.1.0 要交付的是一个可安装、可演示、可测试的本地 MCP 工具权限工作台。用户可以在观察模式记录调用，生成候选策略，在不执行真实工具的情况下回放历史调用，再切换到执行模式进行允许、询问或拒绝。所有决策必须可解释，所有持久化数据必须先脱敏。

第一版只承诺单用户、本机、MCP `stdio`。CLI 必须能够完成全部核心流程；Web 页面只有在 Phase 1 的安全与打包验证通过后才进入 v0.1。任何云服务、多租户、复杂身份系统、网络防火墙和 LLM 安全判断都不属于第一版。

## Goals

- Provide a reliable local workflow for developing and enforcing tool-call permissions.
- Make policies deterministic, explainable, replayable, and versionable.
- Minimize framework lock-in through a normalized internal event model.
- Ship as a complete open-source Python package with examples, tests, documentation, and a secure release path.

## Non-goals

- Operating-system isolation or sandboxing.
- Protecting calls that do not traverse a ToolPermit adapter.
- Detecting every prompt injection, malicious command, or data-exfiltration attempt.
- Managing third-party OAuth credentials.
- Multi-user or organization-wide policy administration.
- Replacing MCP client authentication or authorization.
- Supporting every MCP transport in v0.1.

## Personas

### P1: Agent developer

Needs to connect local tools quickly, observe behavior, and tighten permissions without repeatedly performing destructive actions.

### P2: MCP server maintainer

Needs reusable policy fixtures and regression tests for documented tools and arguments.

### P3: Security reviewer

Needs a bounded threat model, an explainable decision trail, and evidence that candidate policies were replayed against representative calls.

## Required workflows

### W1: Initialize

```bash
toolpermit init
```

Expected outcome:

- Create a documented starter configuration and policy.
- Refuse to overwrite existing files unless explicitly requested.
- Explain observe and enforce modes.

### W2: Observe an MCP server

```bash
toolpermit wrap --mode observe -- python example_server.py
```

Expected outcome:

- Proxy MCP initialization, tool listing, and tool calls.
- Record normalized, redacted events.
- Do not alter upstream decisions in observe mode.
- Display a clear warning that observe mode does not enforce policy.

### W3: Generate a policy draft

```bash
toolpermit policy suggest --from-run RUN_ID --output candidate.yaml
```

Expected outcome:

- Produce a draft based on observed tool names and selected argument constraints.
- Mark the file as generated and inactive.
- Never modify the active policy automatically.
- Flag risky broad patterns for manual review.

### W4: Replay and compare

```bash
toolpermit replay --policy candidate.yaml --baseline current.yaml
```

Expected outcome:

- Execute no upstream tools.
- Show unchanged decisions and transitions such as `allow -> ask`.
- Return a machine-readable report option for CI.
- Use a non-zero exit code when configured regression thresholds fail.

### W5: Enforce

```bash
toolpermit wrap --mode enforce --policy toolpermit.yaml -- python example_server.py
```

Expected outcome:

- Evaluate every supported tool call.
- Forward allowed calls.
- Return a stable denied result for denied calls.
- Pause asked calls until approval, rejection, expiry, or cancellation.
- Fail closed when the policy cannot be loaded or evaluated.

### W6: Approve locally

Expected outcome:

- Show tool name, normalized arguments, redactions, matched rule, and requesting session.
- Approval is bound to the canonical request hash and expires.
- Editing arguments creates a new request; it does not mutate an approval in place.
- Decisions are available through both local UI and CLI.

### W7: Inspect and export

```bash
toolpermit runs list
toolpermit runs show RUN_ID
toolpermit audit export --format jsonl
```

Expected outcome:

- Display redacted records only.
- Support deterministic JSONL export with a schema version.
- Make retention and deletion explicit.

## Functional requirements

### FR-1 Protocol proxy

- Support MCP over local `stdio` for v0.1.
- Preserve request IDs and cancellation semantics across modern discovery and legacy initialization paths.
- Proxy `initialize`, `tools/list`, and `tools/call` correctly.
- Produce explicit errors for unsupported protocol features.

### FR-2 Normalized event model

Each tool-call event must include:

- Schema version.
- Event ID, run ID, ToolPermit connection ID, optional protocol session metadata, and timestamps.
- Client and upstream identifiers where available.
- Tool name and tool-schema fingerprint.
- Canonicalized, redacted arguments.
- Policy version and matched rule ID.
- Decision, explanation, and lifecycle status.
- Upstream duration and redacted outcome metadata when executed.

### FR-3 Policy language

- Versioned YAML format.
- Explicit defaults.
- Stable precedence rules.
- Match tool names and structured argument fields.
- Provide path-oriented conditions without treating string normalization as filesystem containment proof.
- Reject unknown fields by default.
- Support comments and rule IDs.

### FR-4 Decisions

- `allow`: forward the exact call.
- `ask`: create a pending approval for the exact call.
- `deny`: do not call upstream.
- Every decision includes a rule ID and explanation.

### FR-5 Approval lifecycle

- Pending, approved, rejected, expired, cancelled, executed, and failed states.
- Single-use approval token.
- Configurable expiry with a safe default.
- Atomic transition from approved to executing.
- Duplicate messages do not execute the tool twice.

### FR-6 Redaction

- Redact configured keys and recognized credential shapes before persistence.
- Preserve enough structural information for replay.
- Record that redaction occurred without storing the original value.
- Never offer a “reveal original secret” feature because the original is not retained.

### FR-7 Replay

- Evaluate stored normalized calls without starting an upstream server.
- Compare two policy versions.
- Output human-readable tables and JSON.
- Record replay tool version and policy digest.

### FR-8 Policy suggestion

- Derive candidate rules from selected runs.
- Prefer exact tool names and narrow constraints.
- Identify conflicting examples.
- Require manual activation.
- Explain the evidence used for each suggested rule.

### FR-9 Conditional local dashboard

- Bind to loopback by default.
- Show pending approvals and recent runs.
- Filter by decision, tool, session, and rule.
- Require an explicit secure configuration for non-loopback binding.
- This requirement becomes release-blocking only if the Phase 1 UI spike is accepted for v0.1.

### FR-10 Configuration

- One documented configuration file.
- Environment variables only for runtime overrides and secrets.
- Effective configuration inspection with secrets masked.
- Unknown configuration keys fail validation.

## Non-functional requirements

### Security

- Enforcement mode fails closed.
- Redaction precedes storage and display.
- Approval and execution are race-safe.
- Security boundary and exclusions are documented.
- No telemetry by default.

### Reliability

- Unexpected upstream termination produces a clear terminal state.
- Restart does not execute pending calls automatically.
- Database migrations are versioned and tested.
- Interrupted writes do not corrupt the audit database.

### Performance

- Establish a benchmark for policy-decision overhead before release.
- No network access is introduced by ToolPermit except configured upstream/UI communication and explicitly requested update checks, if any.
- UI polling or streaming must not delay tool forwarding.

### Portability

- Support Ubuntu, macOS, and Windows.
- Support Python 3.11 through the versions validated in CI at release time.
- Avoid shell-specific behavior in core workflows.

### Accessibility

- Approval state and risk must not be conveyed by color alone.
- Core tasks remain available from the CLI.
- Web controls have keyboard-accessible labels and focus states.

### Privacy

- Document stored fields, retention, deletion, and export.
- Default to local storage.
- Do not collect usage analytics in v0.1.

## Documentation requirements

- English authoritative README and documentation.
- Chinese README-level feature overview and quickstart.
- Architecture, policy reference, threat model, security model, troubleshooting, and limitations.
- A dangerous-action demo that is contained in a disposable fixture directory.
- No example may require real credentials for the first-run path.

## Release acceptance tests

1. Clean installation from the built wheel on all supported systems.
2. Observe, suggest, replay, and enforce demo completed from documentation.
3. Denied calls never reach the upstream fixture.
4. Expired or replayed approvals never execute.
5. Secret fixtures are absent from the SQLite database, logs, and exported JSONL.
6. Policy parsing failures block enforcement startup.
7. A tool-schema fingerprint change invalidates reusable assumptions.
8. Package metadata, links, license, and version are correct.

## Deferred requirements

- Streamable HTTP adapter.
- Framework-specific SDK hooks.
- Export to native client policy formats.
- Team approval and identity providers.
- Signed/tamper-evident audit chains.
- Container images and Kubernetes deployment.
- Remote policy distribution.
- Advanced DLP, SSRF, and egress inspection.

## Product decisions requiring explicit approval

- Final project and package name.
- License.
- Public compatibility promise.
- Whether the React UI ships in v0.1 or v0.2.
- Whether `ask` or `deny` is the default for unknown tools in the starter policy.
