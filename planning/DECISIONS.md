# Decision Log

> Format: Lightweight architecture/product decision record index  
> Status meanings: `Accepted for planning`, `Proposed`, `Deferred`, `Rejected`, `Superseded`.

## Chinese executive summary

这份文件防止项目在开发过程中反复改变方向。当前已经确认的是：不使用 AgentGate 名称；项目以英文为权威版本；产品核心是可解释、可回放的最小权限策略工作台；第一版本地优先、无遥测、只支持 MCP `stdio`，策略核心不依赖 LLM。

仍待 Phase 1 或项目所有者最终确认的事项包括：正式名称、Apache-2.0 License、React UI 是否进入 v0.1、具体支持的两个 MCP Client，以及是否同时发布容器镜像。尚未确认的决策不能在 README 中写成既定承诺。

## D-001: Product category

- Status: Accepted for planning.
- Decision: Build a policy lifecycle workbench, not a generic agent framework or approval-only gateway.
- Rationale: Existing projects already cover generic approvals and broad MCP firewall features. Observe, explain, suggest, replay, and policy regression form a clearer differentiated workflow.
- Consequence: Runtime mediation is necessary infrastructure but not the complete product story.

## D-002: Reject the AgentGate name

- Status: Accepted.
- Decision: Do not use `AgentGate` as product, repository, package, or CLI name.
- Rationale: Multiple existing GitHub projects use the name in the same product category.
- Consequence: All current references use `ToolPermit` as a provisional working name.

## D-003: Working name ToolPermit

- Status: Proposed.
- Decision: Use `ToolPermit` internally until final availability and collision checks pass.
- Rationale: Short, protocol-neutral, and descriptive of tool authorization.
- Consequence: Public repository/package registration must wait for the final naming gate.

## D-004: English source of truth

- Status: Accepted for planning.
- Decision: English is authoritative for README, reference documentation, schemas, code, API names, issues, and release notes. Chinese initially covers the project overview and quickstart.
- Rationale: Maximizes international open-source accessibility while providing a first-class Chinese entry point without duplicating every document.
- Consequence: Public feature or command changes require checking both language entry points.

## D-005: Local-first and no telemetry

- Status: Accepted for v0.1 planning.
- Decision: Store data locally and send no usage telemetry in v0.1.
- Rationale: Tool calls may contain sensitive data; local-first reduces deployment and privacy complexity.
- Consequence: Product decisions cannot depend on a hosted account, analytics backend, or remote policy service.

## D-006: Deterministic policy core

- Status: Accepted for planning.
- Decision: Core `allow/ask/deny` evaluation and v0.1 policy suggestions do not call an LLM.
- Rationale: Permission decisions must be reproducible, explainable, offline-testable, and inexpensive.
- Consequence: Future optional AI assistance may draft text or suggestions but cannot silently become the enforcement authority.

## D-007: MCP stdio is the only v0.1 transport

- Status: Accepted for planning; validate in Phase 1.
- Decision: Limit the supported runtime boundary to local MCP `stdio`.
- Rationale: Streamable HTTP adds authentication, session, Host/Origin, DNS rebinding, and remote-exposure requirements that would dilute the first release.
- Consequence: The public README must not imply general MCP transport coverage.

## D-008: Python implementation

- Status: Proposed; validate in Phase 1.
- Decision: Implement core, CLI, adapter, API, and packaging in Python 3.11+ using the official MCP Python SDK.
- Rationale: Strong ecosystem fit, rapid development, and alignment with target integrations.
- Consequence: Windows subprocess/stdio behavior is a release-blocking spike.

## D-009: Single-process modular architecture

- Status: Accepted for planning.
- Decision: Build one local application with internal modules and SQLite, not microservices.
- Rationale: Lower operational complexity and clearer trust boundaries for a solo-maintained v0.1.
- Consequence: Component interfaces exist for testability, not distributed deployment.

## D-010: SQLite persistence

- Status: Proposed; validate in Phase 1.
- Decision: Use SQLite for redacted events, policy snapshots, approvals, and migrations.
- Rationale: Local, transactional, portable, and sufficient for a single-user process.
- Consequence: Approval concurrency and crash recovery must be proven with tests.

## D-011: Strict versioned YAML policy

- Status: Proposed.
- Decision: Use a strict, versioned YAML policy parsed with a safe loader and validated against typed models.
- Rationale: Human review and version control matter; unknown keys and ambiguous precedence are unsafe.
- Consequence: No arbitrary code, YAML tags, templating, or OPA/Rego in v0.1.

## D-012: Redact before persistence

- Status: Accepted as a security invariant.
- Decision: Raw sensitive values must not enter durable audit storage.
- Rationale: Post-storage masking does not prevent database, backup, or export disclosure.
- Consequence: Replay uses structurally useful redacted values and cannot reproduce secret-dependent semantics perfectly.

## D-013: Approval bound to exact request

- Status: Accepted as a security invariant.
- Decision: Approval binds to canonical tool name, schema fingerprint, arguments, session, and policy digest; it expires and is single-use.
- Rationale: Approving a broad tool category allows argument substitution and replay.
- Consequence: Any changed field creates a new approval request.

## D-014: UI is not the source of truth

- Status: Accepted for planning.
- Decision: CLI and Web UI call the same application/approval services; core workflows remain available without the UI.
- Rationale: Prevent duplicated security logic and preserve automation/accessibility.
- Consequence: React/Vite remains conditional; a smaller UI can replace it without redesigning core behavior.

## D-015: React/Vite dashboard

- Status: Superseded by Phase 1 validation.
- Decision: Do not add React/Vite to v0.1. Bundle framework-free HTML/CSS/JS assets in the Python wheel and keep all business logic in shared application services.
- Rationale: The packaging spike passed with `importlib.resources`; avoiding a frontend dependency graph lowers build and supply-chain complexity.
- Consequence: Browser-security requirements still apply, but no Node build is required for the production UI.

## D-015A: MCP 2.x protocol posture

- Status: Accepted after Phase 1 local/Linux validation; hosted Windows gate pending.
- Decision: Target MCP Python SDK 2.x, support the 2026-07-28 discovery path, and retain tested legacy initialization compatibility.
- Rationale: MCP 2.0.0 is the stable SDK line and removes mandatory handshake/session assumptions in the modern protocol.
- Consequence: ToolPermit owns run/connection correlation; protocol session IDs are optional metadata.

## D-016: Apache-2.0 license

- Status: Proposed; owner approval required.
- Decision: Prefer Apache-2.0 for broad adoption and an explicit patent grant.
- Alternatives: MIT for simplicity; AGPL-3.0 for strong network copyleft.
- Consequence: No dependency or copied material with incompatible licensing may enter the repository.

## D-017: PyPI-first distribution

- Status: Accepted for planning.
- Decision: Publish the Python package and CLI to PyPI using Trusted Publishing; create matching GitHub Releases.
- Rationale: Natural install path for the Python/MCP audience and a secure OIDC release workflow.
- Consequence: Container image is deferred unless a supported server deployment justifies it.

## D-018: Release completeness

- Status: Accepted for planning.
- Decision: v0.1 requires tests, documentation, community files, threat model, CI, release provenance, examples, and bilingual entry points—not only working code.
- Rationale: The goal is a credible open-source project rather than a demonstration repository.
- Consequence: Missing release gates delay public release.

## D-019: Compatibility promises before 1.0

- Status: Proposed.
- Decision: Document breaking changes and migrations during `0.x`, but do not claim full stability until policy, event, CLI, and database contracts mature.
- Consequence: Every schema and persisted format still requires explicit versioning from the first release.

## D-020: Two-client compatibility target

- Status: Deferred selection.
- Decision needed: Choose two concrete MCP clients for v0.1 integration tests after Phase 1 feasibility review.
- Selection criteria: Public documentation, active maintenance, realistic user demand, and ability to test cancellation/approval behavior.
- Consequence: “Works with MCP clients” remains a bounded claim until targets are named and tested.

## Decision gates before implementation

The project owner should explicitly approve:

1. Product statement and non-goals.
2. Preferred working/final name.
3. Apache-2.0 versus MIT.
4. Python/MCP stdio technical direction.
5. Whether UI is required for v0.1 or conditional.

## Decision gates after Phase 1 spikes

1. Canonical serialization and request-digest algorithm.
2. Policy precedence semantics.
3. SQLite approval transaction/recovery model.
4. UI implementation and packaging.
5. Named MCP client compatibility matrix.
6. Final supported Python versions.
