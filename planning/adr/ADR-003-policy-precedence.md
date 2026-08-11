# ADR-003: Policy precedence and matching

> Status: Accepted for v0.1.

## Chinese summary

策略采用“文件顺序、首条匹配生效”，而不是隐含的“最具体规则”算法。每条规则必须有唯一 ID；默认策略必须显式存在，官方起始配置默认 `ask`。`deny` 决策不能通过审批界面覆盖。无效策略在执行模式启动时直接失败，单次评估错误按 `deny` 处理。

## Context

Most-specific and deny-overrides algorithms sound safe but become difficult to explain when nested conditions interact. Users need a rule order that code review, replay, and generated diffs can reproduce exactly.

## Decision

- Policies have an explicit schema version and explicit default action.
- Rules are evaluated from top to bottom; the first complete match decides.
- Every rule has a unique stable ID and one action: `allow`, `ask`, or `deny`.
- `deny` is terminal and cannot be converted to `allow` through the approval service.
- `ask` creates an exact bound approval request.
- If no rule matches, the explicit default decides; the starter policy uses `ask`.
- Unknown fields, duplicate rule IDs, invalid matchers, and unsupported policy versions fail validation.
- Invalid policy prevents enforce mode from starting.
- Unexpected per-call evaluation failure returns `deny` in enforce mode and a diagnostic-only result in observe/replay mode.
- A linter reports unreachable rules and broad allows that shadow later rules.

Initial matcher surface:

- Exact tool name.
- Exact structured argument value.
- Explicit string glob.
- Lexical path-under matcher with documentation that it is not filesystem containment.

## Consequences

- Moving a rule is a semantic change and must appear in policy review/diff output.
- Deny rules should normally precede broad allow rules; the linter and generated starter policy enforce this guidance.
- There is no hidden specificity score to explain.
- Policy replay can show precisely which rule changed a decision.

## Verification

- Golden precedence table.
- Shadowed-rule linter tests.
- Replay comparison tests for reordered rules.
- Fail-closed validation/evaluation tests.

