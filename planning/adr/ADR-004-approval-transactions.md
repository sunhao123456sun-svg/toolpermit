# ADR-004: Approval transactions and crash recovery

> Status: Accepted for v0.1 after Phase 1 concurrency spike.

## Chinese summary

审批状态存放在 SQLite，以条件更新保证同一审批最多只有一个等待调用进入 `executing`。批准本身不执行工具；原等待调用必须使用相同摘要原子消费批准。进程在执行中崩溃后，重启将状态标记为 `unknown`，绝不自动重试外部副作用。

## Context

Approval, cancellation, expiry, retries, and process crashes can race. A local tool may complete even if its response is lost, so the application cannot promise exactly-once external effects.

## Decision

- Persist the approval lifecycle in SQLite with versioned migrations.
- Use states: `pending`, `approved`, `rejected`, `expired`, `cancelled`, `executing`, `executed`, `failed`, `unknown`.
- Approval validates `pending` state and expiry, then transitions to `approved`.
- The suspended call atomically transitions `approved -> executing` only when ID, request digest, and expiry match.
- Exactly one local consumer may win that conditional update.
- Rejection/cancellation may transition only non-executing states.
- Cancellation during execution is forwarded best-effort; the final state reflects confirmed evidence.
- On restart, all `executing` records become `unknown`; ToolPermit never automatically retries them.
- The UI and CLI call the same application service and transaction path.

## Consequences

- ToolPermit provides at-most-once local approval consumption, not exactly-once upstream side effects.
- Users must investigate `unknown` outcomes.
- SQLite WAL and busy timeout are deployment details; correctness depends on conditional transitions, not on a process-local lock.
- Future distributed/team approval requires a new persistence ADR.

## Verification

- Thirty-two-consumer race test with one winner.
- Digest mismatch and expiry tests.
- Crash-recovery test to `unknown`.
- Cancellation/approval race tests in production suite.

