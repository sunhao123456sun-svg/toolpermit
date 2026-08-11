# Competitive Analysis

> Status: Draft  
> Research date: 2026-08-11  
> Scope: Public GitHub repositories and official project documentation.

## Chinese executive summary

“通用 Agent 审批网关”和“MCP 防火墙”已经是拥挤赛道。`AgentGate` 名称存在直接冲突，且现有项目已经完成读取直通、写入审批、策略、审计和多服务集成。更成熟的安全项目还覆盖 DLP、SSRF、提示词注入检测、签名日志和合规输出。因此，本项目不能以“我们也能拦截并审批工具调用”作为主要卖点。

可行的差异化空位是“策略开发工作台”：标准化记录真实调用、生成最小权限草案、在历史调用上模拟策略变化、解释规则优先级，并以确定性和本地优先为原则。运行时拦截仍然需要，但它是支撑策略生命周期的基础能力，而不是唯一产品价值。

## Evaluation dimensions

Projects were compared on:

- Runtime interception.
- Human approval.
- Policy-as-code.
- Decision explanation.
- Record and replay.
- Least-privilege policy generation.
- Local-first operation.
- Audit and redaction.
- Threat detection and egress control.
- Framework and protocol coverage.

## Landscape

### monteslu/agentgate

Repository: <https://github.com/monteslu/agentgate>

Observed positioning:

- Self-hosted API gateway for agents.
- Read operations execute immediately; writes enter a human approval queue.
- MCP access and service integrations.
- Protects service credentials from the agent.

Implication for ToolPermit:

- `AgentGate` cannot be used as our project name.
- A read/write approval distinction is not sufficient differentiation.
- Service aggregation and credential brokering should not enter our v0.1 scope.

### agentkitai/agentgate

Repository: <https://github.com/agentkitai/agentgate>

Observed positioning:

- Approval workflows for AI agents.
- MCP integration, API keys, scopes, webhooks, policies, and audit logs.
- API-centric request lifecycle.

Implication for ToolPermit:

- Generic approval CRUD, API keys, and audit dashboards are already represented.
- Our approval record must be bound to replayable, normalized tool-call evidence.

### ressl/mcp-firewall

Repository: <https://github.com/ressl/mcp-firewall>

Observed positioning:

- Inline MCP security gateway.
- Policy enforcement, human approval, inbound/outbound detection, DLP, egress control, signed audit trails, and compliance reports.
- YAML and OPA/Rego policy options.

Implication for ToolPermit:

- We should not compete on the number of threat-detection checks.
- We should avoid unverified “enterprise-grade” or compliance claims.
- Our narrow advantage should be policy authoring, simulation, explanation, and developer experience.

### luckyPipewrench/pipelock

Repository: <https://github.com/luckyPipewrench/pipelock>

Observed positioning:

- Agent egress and MCP security proxy.
- DLP, SSRF defenses, prompt-injection scanning, tool poisoning checks, chain detection, and signed receipts.
- Multiple transports and deployment boundaries.

Implication for ToolPermit:

- Network egress inspection is a separate, deep product category.
- v0.1 must not claim to secure traffic it cannot mediate.

### eunomia-bpf/agentsight

Repository: <https://github.com/eunomia-bpf/agentsight>

Observed positioning:

- System-level local-first observability for agent processes, files, networks, resources, model calls, and tool activity.

Implication for ToolPermit:

- System observability is broader and lower-level than our intended boundary.
- ToolPermit should expose stable events that observability tools could consume rather than reproducing eBPF/system profiling.

### OpenAI Agents SDK and LangGraph

Repositories:

- <https://github.com/openai/openai-agents-python>
- <https://github.com/langchain-ai/langgraph>

Observed positioning:

- Agent runtimes already support tools, sessions, tracing, persistence, and human-in-the-loop patterns.

Implication for ToolPermit:

- ToolPermit should integrate with runtimes rather than become another agent framework.
- Its event schema and policy engine should remain usable without adopting a particular orchestration model.

## Comparative matrix

Legend: strong native focus = `●`; present but not central = `◐`; not evident in initial review = `○`.

| Capability | AgentGate projects | MCP Firewall | Pipelock | AgentSight | ToolPermit target |
|---|---:|---:|---:|---:|---:|
| Runtime interception | ● | ● | ● | ◐ | ● |
| Human approval | ● | ● | ◐ | ○ | ● |
| Policy as code | ● | ● | ● | ○ | ● |
| Rule-level explanation | ◐ | ◐ | ◐ | ○ | ● |
| Historical policy replay | ○ | ◐ | ◐ | ◐ | ● |
| Least-privilege draft generation | ○ | ○ | ◐ | ○ | ● |
| Policy regression testing | ○ | ◐ | ◐ | ○ | ● |
| DLP/egress threat detection | ○ | ● | ● | ◐ | limited |
| Local-first | ● | ● | ● | ● | ● |
| Multi-service credential broker | ● | ○ | ○ | ○ | ○ |

The matrix is a product-positioning aid, not a security certification or exhaustive feature audit.

## Identified gap

The defensible gap is a policy lifecycle rather than a larger firewall:

```text
Observe -> Normalize -> Draft -> Explain -> Replay -> Diff -> Enforce -> Audit
```

ToolPermit should own this workflow end to end for MCP tool calls.

## Differentiation requirements

The project should not be released unless it demonstrates all of the following:

1. A normalized event format independent of one agent runtime.
2. Deterministic rule evaluation with stable explanations.
3. Replay of stored calls against candidate policies without executing upstream tools.
4. A policy diff that identifies newly allowed, newly denied, and newly approval-gated calls.
5. A least-privilege draft generator that never silently activates generated permissions.
6. Redaction before persistence.
7. A documented boundary explaining what ToolPermit does not secure.

## Positioning to avoid

- “The firewall for all AI agents.”
- “Enterprise-grade security” without independent validation.
- “Stops prompt injection.”
- “Makes MCP safe.”
- “Zero-trust” as a marketing label without identity and trust-boundary definitions.
- Feature-count comparisons that cannot be maintained.

## Risks

- Existing projects may add replay and policy generation.
- MCP clients may implement stronger native approval controls.
- Tool-call normalization may lose protocol-specific security context.
- Users may incorrectly treat the proxy as a sandbox.
- A generic YAML policy language can become complex and hard to stabilize.

## Response strategy

- Publish a stable event schema and policy semantics early.
- Build fixtures and conformance tests that are useful beyond the UI.
- Keep adapters thin and the policy core protocol-neutral.
- Document limitations next to quickstart examples.
- Measure decision overhead and compatibility instead of making broad security claims.

## Research follow-ups before v0.1

- Perform a source-level comparison of policy precedence and approval binding in the closest three projects.
- Review current MCP authorization, elicitation, and transport-security guidance.
- Test at least two MCP clients for cancellation and approval-resume behavior.
- Re-run the landscape review immediately before publishing the public README.

