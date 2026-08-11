# Threat Model

> Status: Initial design threat model  
> Applies to: ToolPermit v0.1 local single-user deployment  
> Review trigger: Any new transport, remote access mode, credential store, or multi-user feature.

## Chinese executive summary

ToolPermit 的安全边界是“经过它代理的 MCP 工具调用”，不是整个 Agent、操作系统或网络。第一版假设本机用户和安装的软件基本可信，但 Agent 输出、MCP Server、工具描述、工具参数和返回内容都可能不可信。执行模式必须 Fail-closed，审批必须绑定到精确请求并且只能使用一次，数据必须在持久化之前脱敏。

最主要风险包括：调用绕过代理、恶意 Server、参数规范化差异、审批后参数被替换、重复执行、策略优先级错误、日志泄密、UI 被跨站请求利用、符号链接或 TOCTOU 导致实际操作超出策略理解，以及用户误把 ToolPermit 当成系统沙箱。v0.1 的文档和 UI 必须持续展示这些边界。

## Security objectives

1. A denied tool call does not reach the mediated upstream server.
2. An asked tool call executes only after a valid, unexpired, single-use approval bound to the exact canonical request.
3. Policy evaluation is deterministic and explainable.
4. Policy or configuration failure cannot silently disable enforcement.
5. Sensitive values are redacted before durable storage.
6. Restart, retries, cancellation, and duplicate messages do not cause unintended execution.
7. Users can distinguish observe mode from enforcement mode.
8. The product accurately communicates what it does not protect.

## Out of scope security properties

ToolPermit v0.1 does not guarantee:

- Isolation of the MCP server process.
- Prevention of direct calls that bypass ToolPermit.
- Protection from a compromised operating system or local administrator.
- Correctness or safety of an allowed upstream tool.
- Complete prompt-injection, malware, DLP, or data-exfiltration detection.
- Filesystem containment when the upstream server resolves symlinks or changes state after evaluation.
- Authentication between arbitrary remote users and services.
- Integrity of data exported and later modified outside ToolPermit.

## System and trust boundaries

```text
Untrusted/partially trusted                     Trusted for v0.1

Agent output and model reasoning ----┐
MCP client messages -----------------+--> [ToolPermit process]
MCP tool schemas/descriptions -------+          |
Tool arguments ----------------------+          +--> [Local SQLite]
Tool results ------------------------+          +--> [Loopback UI]
Upstream MCP server -----------------┘

Local OS/user account is a deployment assumption, not a boundary ToolPermit enforces.
```

### Trusted components

- Installed ToolPermit release and its pinned dependencies.
- Active policy selected by the user.
- Local database file permissions, subject to the host OS.
- Local user operating the approval UI or CLI.

### Untrusted inputs

- All MCP messages and metadata.
- Tool names, schemas, annotations, and descriptions.
- Tool-call arguments and results.
- Imported policy files and recorded-event files until validated.
- Browser requests, even when the UI is bound to loopback.
- Environment variables and command-line values.

## Assets

- Integrity of policy decisions.
- User files and external systems reachable through upstream tools.
- Secrets present in arguments, results, environment, or configuration.
- Approval authority.
- Audit-record confidentiality and integrity.
- Availability of the agent workflow.
- Package and release supply-chain integrity.

## Threat actors

1. A compromised or manipulated agent producing malicious tool calls.
2. A malicious or compromised MCP server.
3. Untrusted content embedded in tool descriptions or results.
4. A local web page attempting to reach the loopback approval UI.
5. A malicious dependency or compromised release workflow.
6. An accidental operator making a broad policy or approval decision.

## Threat scenarios and mitigations

| ID | Threat | Impact | v0.1 mitigation | Residual risk |
|---|---|---|---|---|
| T-01 | Client calls upstream directly and bypasses ToolPermit | No policy enforcement | Document mediated boundary; generate explicit wrapper config; show active connection status | Cannot prevent external bypass |
| T-02 | Unknown tool is treated as allowed | Unreviewed execution | Explicit default; safe starter policy; enforcement fails closed | User may configure broad defaults |
| T-03 | Tool schema changes after policy creation | Policy meaning drifts | Fingerprint schema; log changes; require fresh decision/approval | Semantically malicious compatible schemas remain possible |
| T-04 | Arguments differ between evaluation and execution | Approval bypass | Canonical request object; immutable payload; request digest checked immediately before execution | Upstream may reinterpret values |
| T-05 | Approval request is replayed | Duplicate side effect | Single-use nonce; expiry; atomic state transition; idempotency tests | Upstream side effect may occur despite lost response |
| T-06 | Concurrent workers execute one approval twice | Duplicate side effect | Database transaction/compare-and-swap state transition | External retry semantics still require care |
| T-07 | Policy parse/evaluation error falls back to allow | Arbitrary execution | Refuse enforcement startup; per-call evaluation errors deny | Availability loss is intentional |
| T-08 | Rule precedence is ambiguous | Unexpected allow | One documented algorithm; rule IDs; linter; golden tests | Complex policies can still confuse users |
| T-09 | Secret appears in logs/database/export | Credential disclosure | Redact structured values before persistence; log filters; secret fixtures in tests | Unknown secret formats may pass through |
| T-10 | Tool result contains prompt injection | Agent manipulation | Treat result as untrusted; document that v0.1 does not sanitize semantic content | Agent may act on malicious content later |
| T-11 | Malicious tool name/description injects UI content | UI compromise | Escape output; restrictive CSP; no raw HTML rendering | Browser or dependency defects |
| T-12 | Cross-site request targets loopback UI | Unauthorized approval | CSRF protection; SameSite cookies; Origin/Host validation; no permissive CORS | Compromised browser profile/local process |
| T-13 | Non-loopback UI is exposed without auth | Remote approval access | Refuse non-loopback bind without explicit auth configuration | Misconfigured reverse proxy |
| T-14 | Path rule appears to contain access but symlink escapes | Unauthorized file access | State that lexical path policies are not a filesystem sandbox; optional upstream-aware checks later | Upstream controls actual filesystem resolution |
| T-15 | Time-of-check/time-of-use state changes | Approved action differs in effect | Bind exact args and execute promptly; expose expiry; document semantic TOCTOU | External state cannot be frozen |
| T-16 | Database is modified by local process | Audit tampering | File permissions; schema validation; optional integrity hashes deferred | Local account compromise is out of scope |
| T-17 | Observe mode is mistaken for enforcement | False sense of safety | Persistent UI/CLI banner and audit field; distinct command output | User may ignore warning |
| T-18 | Oversized/deep input exhausts resources | Denial of service | Message size/depth limits; bounded logs; timeouts | Local availability attacks remain possible |
| T-19 | Upstream hangs or exits mid-call | Stuck workflow or retry confusion | Timeout/cancellation; terminal state; no automatic side-effect retry | Unknown upstream completion state |
| T-20 | Malicious policy import uses unexpected YAML behavior | Code execution or policy confusion | Safe YAML parser; strict schema; reject tags/unknown keys | Resource exhaustion from crafted input |
| T-21 | Release credential is stolen | Supply-chain compromise | PyPI Trusted Publishing; protected release environment; least-privilege Actions permissions | Compromised maintainer or CI dependency |
| T-22 | GitHub Action from PR accesses release secrets | Supply-chain compromise | No release on untrusted PR; pin actions; protected environment | Compromised pinned action or maintainer |

## Policy decision invariants

1. A call has one canonical representation for evaluation, approval, audit, and execution.
2. `deny` cannot be overridden by an approval action.
3. A more specific matching rule does not implicitly win unless the versioned policy algorithm says so.
4. Policy evaluation returns a decision or a closed error; it never returns “unknown, therefore allow.”
5. Generated rules remain inactive until explicitly selected by the operator.
6. Redacted values cannot be reconstructed from persisted ToolPermit data.

## Approval invariants

- Request digest includes normalized tool name, schema fingerprint, canonical arguments, ToolPermit run/connection correlation, and policy digest.
- Approval has a creation time, expiry, actor, and one terminal outcome.
- Changed arguments always produce a new digest and approval request.
- Restart never converts pending approval into approved.
- Cancellation before execution prevents transition to executing.
- UI and CLI use the same backend transition logic.

## Data classification

| Data | Default storage | Treatment |
|---|---|---|
| Tool name and schema fingerprint | Stored | Non-secret metadata; validate length/encoding |
| Tool arguments | Redacted then stored | Configurable key/pattern redaction |
| Tool results | Metadata by default | Full content opt-in only in a future design review |
| Prompt/model messages | Not stored | Outside v0.1 audit scope |
| Approval actor | Local identifier | Avoid collecting unnecessary personal data |
| Configuration secrets | Not stored in audit | Mask in effective-config output |

## Security verification plan

- Unit tests for precedence, closed errors, digests, expiry, and state transitions.
- Property-based tests for canonicalization and policy parsing.
- Concurrency tests proving at-most-once approval consumption inside ToolPermit.
- Malicious fixtures for YAML, JSON-RPC, HTML, paths, logs, and oversized input.
- Database inspection tests ensuring raw secret fixtures never persist.
- E2E tests for CSRF, Origin/Host validation, loopback defaults, and non-loopback refusal.
- Dependency and CodeQL scans in CI.
- A pre-release manual threat-model review.

## Required security documentation

- `SECURITY.md` with private vulnerability reporting instructions.
- Security model and limitations in the public docs.
- Supported-version policy.
- Deployment guide that separates local use from unsupported remote exposure.
- A warning in every dangerous-action example.

## Deferred hardening

- Tamper-evident audit chains.
- OS-level sandbox integration.
- Remote identity providers and RBAC.
- Network egress mediation.
- Advanced DLP and semantic injection classifiers.
- Reproducible builds beyond source and artifact provenance.
