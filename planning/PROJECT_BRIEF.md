# ToolPermit Project Brief

> Status: Draft for Phase 0 review  
> Working name: ToolPermit  
> Source of truth: English; the Chinese summary is provided for project-owner review.

## Chinese executive summary

ToolPermit 是一个本地优先、与智能体框架无关的工具权限工作台。它位于 AI Agent/MCP Client 与 MCP Server 之间，记录标准化的工具调用，使用确定性策略作出 `allow`、`ask` 或 `deny` 决策，并允许开发者用历史记录回放、解释和测试策略。项目的核心差异不是再做一个审批队列，而是帮助开发者从真实使用记录中形成可审计、可测试的最小权限策略。

首个公开版本聚焦本地单用户、MCP `stdio`、YAML 策略、CLI 审批、脱敏审计、记录回放和策略建议；如果 Phase 1 的安全与打包验证通过，再加入本地网页审批界面。项目不承诺提供操作系统沙箱、企业合规平台或基于 LLM 的绝对安全判断。

## Problem

AI agents can invoke tools that read files, execute commands, call APIs, and modify external systems. Developers currently face four connected problems:

1. Tool permissions are often broad, static, and difficult to review.
2. Approval prompts show an action but rarely explain the policy decision behind it.
3. Tightening a policy can break workflows, yet teams lack a safe way to replay historical calls against a candidate policy.
4. Audit logs may expose secrets and are commonly tied to one agent framework.

Existing gateways already cover generic approval queues and runtime blocking. ToolPermit will focus on the missing developer workflow: observe, explain, derive, simulate, then enforce least privilege.

## Product statement

ToolPermit is a local-first policy workbench for AI agent tool calls. It records normalized tool usage, generates least-privilege policy drafts, simulates policy changes against historical traces, and enforces `allow`, `ask`, or `deny` at the MCP boundary.

## Target users

### Primary

- Individual AI-agent developers using local MCP servers.
- MCP server authors who need reproducible permission tests.
- Developers integrating tools into OpenAI Agents SDK, LangGraph, Codex, Claude, Cursor, or similar clients.

### Secondary

- Security engineers reviewing an agent prototype before wider deployment.
- Open-source maintainers who want safe, demonstrable tool-use examples.

### Not targeted in v0.1

- Large enterprises requiring multi-tenant identity, centralized policy distribution, or compliance reporting.
- End users seeking a general-purpose desktop automation product.
- Workloads requiring an operating-system or container sandbox.

## Jobs to be done

1. When I connect a new MCP server, help me observe what tools the agent actually uses without immediately blocking development.
2. When I move from experimentation to enforcement, help me generate a narrow policy draft from observed calls.
3. When I edit a policy, show which recorded calls change from allowed to asked or denied before I deploy it.
4. When a call is blocked or paused, explain the exact rule, condition, and precedence that produced the decision.
5. When I investigate an incident, provide a local, redacted, exportable audit trail.

## Value proposition

- **Deterministic:** core decisions do not require an LLM.
- **Explainable:** every decision returns a rule ID and reason.
- **Testable:** policies have fixtures, replay, and regression checks.
- **Local-first:** no mandatory cloud account or telemetry.
- **Framework-neutral:** normalized events and a narrow MCP boundary reduce framework coupling.
- **Least-privilege oriented:** observed behavior informs policy drafts but never silently grants permissions.

## Product principles

1. Fail closed in enforcement mode.
2. Never confuse a policy proxy with a sandbox.
3. Approval applies to an exact action, not a vague tool category.
4. Redact before persistence, not after display.
5. Unknown and changed tools require explicit treatment.
6. Prefer deterministic rules over probabilistic safety claims.
7. Make the safe path easy to understand and test.
8. Keep the core useful without a web UI or model API key.

## Initial user journey

1. Install ToolPermit from PyPI.
2. Wrap a local MCP server in observe mode.
3. Run normal agent tasks.
4. Inspect normalized, redacted calls.
5. Generate a candidate policy.
6. Edit and replay the candidate against the recorded dataset.
7. Switch to enforcement mode.
8. Approve or reject exceptional actions from the CLI or, when the UI spike is accepted, the local UI.

## Success measures for v0.1

- A new user can run the bundled demo within ten minutes from a clean environment.
- The same event and policy produce the same decision across supported platforms.
- Every enforced decision includes a stable rule ID and human-readable explanation.
- Historical replay reports all decision changes between two policy versions.
- Sensitive fixture values are redacted before they reach persistent storage.
- Core policy-engine branch coverage is at least 90%; project-wide coverage is at least 80%.
- CI passes on Ubuntu, macOS, and Windows for supported Python versions.
- Two independent MCP clients complete the documented demo flow.

## Constraints

- Solo-maintainer-friendly architecture and release process.
- No required paid service.
- English documentation is authoritative; Chinese coverage initially includes the project overview and quickstart.
- The working name remains provisional until package, repository, domain, and trademark checks are completed.

## Open questions

- Whether the first UI should use React/Vite or a smaller server-rendered implementation.
- Whether v0.1 should publish a container image in addition to a Python package.
- Which two MCP clients will form the first compatibility target.
- Whether generated policies should support only native YAML or include one export adapter in v0.1.

## Phase 0 exit criteria

- Positioning is demonstrably different from existing approval gateways and MCP firewalls.
- Scope, non-goals, threat model, architecture, and release gates agree with one another.
- The working name passes an initial availability screen.
- High-risk technical assumptions have explicit Phase 1 spikes.
- The project owner approves the v0.1 definition before implementation begins.
