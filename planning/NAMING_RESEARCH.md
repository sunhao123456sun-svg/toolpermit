# Naming Research

> Status: Preliminary screen only  
> Research date: 2026-08-11  
> Important: Search absence does not establish legal availability or ownership.

## Chinese executive summary

`AgentGate` 已确定不能使用：GitHub 上至少有两个同名且功能高度重合的项目。当前推荐工作名是 `ToolPermit`，因为它直接表达“工具调用需要明确授权”，拼写简单，初步检查没有发现完全同名的主要 GitHub 仓库，PyPI 和 npm 查询在检查时均返回未注册状态。

这些结果只是初筛。GitHub 搜索会变化，包名可能随时被注册，域名和商标尚未完成正式检查。因此现阶段所有文档都要标注 “working name”，正式创建公开仓库和发布包之前必须复核并保留两个备选名称。

## Naming criteria

A viable name should:

- Be short enough for a CLI command and Python package.
- Be easy to spell and pronounce for English and Chinese users.
- Describe permissions/policy without claiming complete security.
- Avoid collision with established agent, security, IAM, and MCP products.
- Allow consistent repository, package, executable, and documentation naming.
- Avoid “MCP” in the core brand so future protocol adapters remain possible.

## Rejected name

### AgentGate

Decision: Reject.

Reasons:

- Existing repository: <https://github.com/monteslu/agentgate>
- Existing repository: <https://github.com/agentkitai/agentgate>
- Both operate in agent approval/gateway territory.
- Search discoverability and user confusion would be unacceptable.

## Candidate screen

### 1. ToolPermit

Proposed brand: `ToolPermit`  
Proposed repository: `toolpermit`  
Proposed PyPI package: `toolpermit`  
Proposed CLI: `toolpermit`

Strengths:

- Directly describes tool authorization.
- Short and readable.
- Does not restrict the brand to MCP.
- Supports product language such as “permit”, “policy”, and “decision.”

Weaknesses:

- “Permit” may suggest a simple allowlist unless positioning emphasizes observe/replay/explain.
- Descriptive names can be harder to protect as a brand.

Initial screen on 2026-08-11:

- GitHub: no exact-name repository found in the initial search; recheck required because the unauthenticated API later rate-limited further searches.
- PyPI JSON endpoint for `toolpermit`: HTTP 404 at check time.
- npm registry endpoint for `toolpermit`: HTTP 404 at check time.
- Domains: not verified with a registrar.
- Trademarks/company names: not legally reviewed.

Recommendation: Preferred working name, not yet final.

### 2. AgentPolicyLab

Proposed CLI/package: `agentpolicylab`

Strengths:

- Strongly communicates experimentation and policy simulation.
- Differentiates from a runtime-only firewall.

Weaknesses:

- Long CLI name.
- “Lab” can make a production-capable tool sound experimental.
- Less direct than ToolPermit.

Initial screen:

- No exact-name repository found in the initial GitHub search.
- PyPI and npm endpoints returned HTTP 404 at check time.
- Domain and trademark checks pending.

Recommendation: Reserve as a descriptive fallback.

### 3. ToolPolicyLab

Strengths:

- Accurately describes the workbench focus.
- Protocol-neutral.

Weaknesses:

- Long and generic.
- Less memorable as a product.

Initial screen:

- PyPI and npm endpoints returned HTTP 404 at check time.
- GitHub exact-name confirmation, domain, and trademark checks pending.

Recommendation: Documentation phrase, not preferred brand.

### 4. PermitForge

Strengths:

- Memorable and compatible with policy generation.
- Short CLI/package name.

Weaknesses:

- Does not clearly indicate AI agents or tools.
- Could collide with unrelated permitting, construction, or IAM products.

Initial screen:

- PyPI and npm endpoints returned HTTP 404 at check time.
- GitHub exact-name confirmation, domain, and trademark checks pending.

Recommendation: Secondary brand fallback only after broader search.

## Recommended naming hierarchy

1. `ToolPermit` — preferred working name.
2. `AgentPolicyLab` — fallback if ToolPermit becomes unavailable.
3. `PermitForge` — fallback only after a broader collision review.

## Naming architecture

If ToolPermit is approved:

| Surface | Name |
|---|---|
| Product | ToolPermit |
| GitHub repository | `toolpermit` |
| Python distribution | `toolpermit` |
| Python import | `toolpermit` |
| CLI | `toolpermit` |
| Configuration | `toolpermit.yaml` |
| Local data directory | Platform-appropriate `toolpermit` app-data path |
| Environment prefix | `TOOLPERMIT_` |

Avoid creating multiple package names in v0.1 unless package ownership requires it.

## Tagline candidates

Preferred:

> Explainable least-privilege policies for AI agent tools.

Long form:

> Observe, replay, and enforce AI agent tool permissions locally.

Chinese:

> 为 AI 智能体工具调用提供可解释的最小权限策略。

## Final verification checklist

Immediately before creating the public repository:

- [ ] Re-run exact and fuzzy GitHub repository search.
- [ ] Search GitHub organizations and user names.
- [ ] Confirm PyPI project ownership/availability.
- [ ] Confirm npm name only if an npm package is planned.
- [ ] Check crates.io, Homebrew, Docker Hub, and GHCR naming if relevant.
- [ ] Search general web results and major social accounts.
- [ ] Check relevant domain names with a registrar; DNS absence is not proof of availability.
- [ ] Search major trademark databases and company-name databases appropriate to intended markets.
- [ ] Check pronunciation, spelling, and unwanted meanings in English and Chinese.
- [ ] Reserve the repository and package name close together to reduce squatting risk.
- [ ] Update every planning document from “working name” to the accepted name.

## Decision rule

Do not select a weaker name solely because a preferred domain is unavailable. The GitHub repository, Python package, CLI clarity, and collision risk matter more than owning a perfect `.com` for v0.1.

