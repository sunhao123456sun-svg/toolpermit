# MVP Scope

> Target: ToolPermit v0.1.0  
> Purpose: Prevent scope drift and define a release-complete, not feature-complete, first version.

## Chinese executive summary

MVP 不是只有几段代理代码的 Demo，而是一个能从 PyPI 安装、有测试、有文档、有安全说明、能完整演示观察—建议—回放—执行流程的首个公开版本。功能上只支持本地单用户和 MCP `stdio`，但工程质量按正式开源项目要求执行。

决定 MVP 是否成功的不是“支持多少 Agent 框架”，而是用户能否在十分钟内运行示例、理解一次决策为什么发生、验证策略变化不会意外扩大权限，并确认敏感测试值没有落盘。

## Release thesis

v0.1 proves one narrow claim:

> Developers can develop and enforce explainable least-privilege policies for local MCP tool calls using recorded evidence and offline replay.

Anything that does not directly prove this claim is deferred unless required for safety, packaging, or maintainability.

## In scope

### Core product

- Local single-user application.
- MCP `stdio` proxy for the supported message subset.
- Observe, enforce, and replay modes.
- Versioned strict YAML policy format.
- `allow`, `ask`, and `deny` decisions.
- Stable rule IDs and explanations.
- Tool-schema fingerprints.
- Exact approval binding, expiry, rejection, cancellation, and single-use execution.
- Redacted SQLite audit storage.
- JSONL audit export.
- Offline replay and policy comparison.
- Deterministic least-privilege policy draft generation.
- CLI for all core workflows.
- Minimal loopback approval/run-inspection UI if the Phase 1 UI spike is accepted.

### Engineering completeness

- Typed Python package.
- Versioned database migrations.
- Unit, integration, protocol, security, and E2E tests.
- Ubuntu, macOS, and Windows CI.
- Documentation build and link checks.
- Package build and clean-install smoke tests.
- Private vulnerability-reporting instructions.
- GitHub issue/PR templates and contribution guide.
- Dependabot, CodeQL, secret scanning configuration, and protected release workflow.

### Documentation

- English README and authoritative docs.
- Chinese project overview and quickstart.
- Architecture and security boundaries.
- Policy reference.
- CLI reference.
- Troubleshooting and known limitations.
- Safe filesystem demo using only a disposable fixture directory.

## Conditionally in scope

These ship in v0.1 only if their spike passes without threatening the release thesis:

### React/Vite dashboard

Accept when:

- Static assets can be built reproducibly and bundled in the wheel.
- The UI does not create a second source of business logic.
- CSRF, CSP, Host, Origin, and loopback tests are practical.

Fallback:

- Server-rendered minimal UI or CLI-only approval for v0.1, with the richer dashboard moved to v0.2.

### Container image

Accept when:

- It serves a real supported deployment rather than a badge/checklist goal.
- Image scanning, non-root execution, and provenance are configured.

Default:

- Defer until Streamable HTTP or a supported remote/server deployment exists.

### One policy export adapter

Accept when:

- A target client has a stable documented permission format.
- Semantics can be mapped without pretending unsupported constraints are enforced.

Default:

- Native ToolPermit YAML only in v0.1.

## Out of scope

- Streamable HTTP proxy.
- SSE legacy transport.
- Remote dashboard access.
- User accounts, organizations, RBAC, SSO, or OAuth.
- Hosted control plane or telemetry service.
- Credential vault or external-service connector catalog.
- OPA/Rego.
- Kubernetes, sidecars, or fleet management.
- SIEM, SOC 2, DORA, or other compliance reports.
- Signed/tamper-evident audit chains.
- OS-level process sandbox.
- Network egress proxy, SSRF firewall, or DNS controls.
- Semantic prompt-injection classifier.
- LLM-based policy decisions.
- Automatic activation of generated policy.
- Complete storage of prompts or tool results.
- Mobile UI.
- Plugin marketplace.

## Epic breakdown

### E0: Repository foundation

Deliverables:

- Public-facing file structure.
- Packaging skeleton.
- Quality tools and CI.
- Community health files.

Exit condition:

- Empty package builds and installs on the CI matrix.

### E1: Domain and policy core

Deliverables:

- Versioned types and policy schema.
- Parser, validation, precedence, decision, and explanation.
- Golden and property-based tests.

Exit condition:

- Pure policy suite passes without MCP, database, or web dependencies.

### E2: MCP mediation

Deliverables:

- Upstream process supervision.
- Supported MCP message proxying.
- Tool catalog and call normalization.
- Observe mode.

Exit condition:

- Bundled client/server fixture completes initialize, list, call, cancel, and shutdown tests on all supported systems.

### E3: Enforcement and approval

Deliverables:

- Enforce mode.
- Approval state machine and exact request digest.
- CLI approval.
- Crash and duplicate-message behavior.

Exit condition:

- Security tests prove denied, expired, altered, and replayed calls do not execute.

### E4: Audit and replay

Deliverables:

- Redaction boundary.
- SQLite schema and migrations.
- Run inspection and JSONL export.
- Offline replay and policy diff.

Exit condition:

- Secret fixtures never persist and replay starts no upstream process.

### E5: Policy suggestion

Deliverables:

- Deterministic grouping and evidence selection.
- Inactive candidate policy output.
- Conflict and broad-rule warnings.

Exit condition:

- Generated candidates are reproducible and require explicit activation.

### E6: Local UI

Deliverables:

- Pending approvals.
- Recent runs and decision detail.
- Security headers and browser protections.

Exit condition:

- UI and CLI drive the same tested approval service; non-loopback access is refused by default.

### E7: Documentation and examples

Deliverables:

- English docs, Chinese overview/quickstart, disposable demo, limitations, screenshots/GIF.

Exit condition:

- A clean-room user completes the documented flow in ten minutes without credentials.

### E8: Release hardening

Deliverables:

- Security review, benchmarks, package provenance, release automation, TestPyPI rehearsal.

Exit condition:

- All release gates in [RELEASE_PLAN.md](RELEASE_PLAN.md) pass.

## Phase 1 technical spikes

No production implementation should begin until these spikes answer their questions:

| Spike | Question | Pass condition |
|---|---|---|
| S1 stdio mediation | Can one Python process transparently supervise and proxy the required MCP flow on all target OSes? | Fixture suite passes on Ubuntu/macOS/Windows |
| S2 pause/resume | Can `ask` suspend a call without breaking IDs, cancellation, or client timeouts? | Two target clients complete approve/reject/cancel paths |
| S3 canonical digest | Can equivalent structured inputs produce stable digests without ambiguity? | Golden vectors and property tests pass |
| S4 SQLite lifecycle | Can approval be consumed atomically and recover safely after interruption? | Concurrency/crash tests show no double transition |
| S5 UI packaging | Can a secure local UI be bundled without making install/build fragile? | Clean wheel install serves tested assets |
| S6 redaction/replay | Can stored events retain policy-test value after secrets are irreversibly redacted? | Representative fixtures replay with no raw secret persisted |

## Definition of done for every feature

- Acceptance criteria are documented.
- Threat-model impact is reviewed.
- Runtime code is typed and tested.
- Error and cancellation behavior are explicit.
- User-facing English documentation is updated.
- Chinese overview is updated when the public feature list or quickstart changes.
- No new dependency is added without purpose and license review.
- CI passes from a clean checkout.

## v0.1 release gates

### Product

- Complete observe -> suggest -> replay -> enforce demo.
- Clear decision explanation and policy diff.
- No high-severity known defect in the supported workflow.

### Security

- Threat model reviewed against implementation.
- Fail-closed and approval-binding tests pass.
- Secret persistence tests pass.
- `SECURITY.md` and supported-version policy published.

### Quality

- All required CI checks pass.
- Core coverage >= 90%; total coverage >= 80%.
- No unexplained type-check suppressions in security-critical code.
- Clean install and uninstall verified.

### Documentation

- English source of truth complete.
- Chinese overview and quickstart correspond to release version.
- Known limitations visible from README.
- Demo uses no real credentials or user directories.

### Distribution

- TestPyPI rehearsal succeeds.
- Trusted Publishing and protected release environment configured.
- GitHub release artifacts and provenance generated.
- Package name and links verified immediately before release.

## Post-v0.1 candidate order

1. Streamable HTTP security design and adapter.
2. Native integrations/export adapters based on user demand.
3. Tamper-evident audit option.
4. Team approval and remote identity only after a new threat model.
5. Advanced output/egress controls through integration, not immediate reimplementation.
