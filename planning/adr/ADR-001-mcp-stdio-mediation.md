# ADR-001: MCP stdio mediation

> Status: Accepted for v0.1 after Phase 1 local/Linux validation; hosted Windows validation pending.

## Chinese summary

v0.1 使用行级双向 MCP `stdio` 代理，而不是重新实现 Agent 框架或用高层 SDK 终止并重建整个协议。ToolPermit 只对需要治理的 `tools/call` 和取消流程做结构化处理，其余合法消息尽量透明转发。现代 `server/discover` 与旧 `initialize` 都必须通过测试。

## Context

ToolPermit must mediate a local MCP server without coupling policy behavior to one agent runtime. The MCP 2.x SDK supports both the 2026-07-28 discovery flow and older initialization flow. Approval can suspend a tool call, so the client reader must continue processing cancellation and unrelated messages while that call waits.

## Decision

- Launch the upstream MCP server as a supervised child process.
- Maintain independent client-to-upstream and upstream-to-client pumps.
- Parse each newline-delimited JSON-RPC message with a bounded line size.
- Intercept supported `tools/call` requests into immutable ToolPermit domain objects.
- Handle recognized cancellation messages against pending calls before forwarding.
- Observe tool discovery/list responses to maintain a schema fingerprint catalog.
- Forward other valid messages without semantic reimplementation.
- Reject malformed or oversized messages with a protocol-safe failure; never persist the raw invalid payload.
- Test modern `server/discover`, legacy `initialize`, list, call, cancellation, upstream exit, and shutdown.
- Support only local `stdio` in v0.1.

## Consequences

- The adapter can remain framework-neutral and preserve protocol evolution better than a full reimplementation.
- Per-call tasks and serialized pipe writes are required.
- Transparent forwarding does not make unsupported features governed; documentation must distinguish “forwarded” from “mediated.”
- Streamable HTTP requires a separate ADR and threat-model review.

## Verification

- Python MCP 2.0 modern and legacy fixture tests.
- Independent TypeScript MCP 1.30 client test.
- Cancellation-before-forward test.
- Three-OS hosted workflow before Phase 1 closes.

