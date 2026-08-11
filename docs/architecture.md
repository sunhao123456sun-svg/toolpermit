# Architecture

ToolPermit has one security decision path shared by the protocol adapter, CLI, and local UI.

```text
MCP client
    │ JSON-RPC over stdio
    ▼
MCP proxy ── normalize ──► policy engine ── allow/ask/deny
    │                          │
    │                          ├──► approval service (SQLite transaction)
    │                          └──► redacted audit store
    ▼
MCP stdio server

CLI / loopback UI ──► shared application service ──► audit + approvals + replay + suggestion
```

## Dependency boundaries

- `domain` contains immutable call, decision, and approval-state types.
- `policy` parses and evaluates strict policy without database, network, subprocess, UI, or clock
  access.
- `canonical` creates typed policy/schema/approval digests.
- `redaction` irreversibly transforms values before persistence.
- `audit` owns monotonic SQLite migrations and deterministic export.
- `approvals` owns race-safe single-use state transitions.
- `replay` and `suggest` operate on stored redacted events without upstream execution.
- `protocol/mcp` converts supported MCP JSON-RPC traffic and supervises the upstream process.
- `application` is the shared orchestration boundary for CLI and web use cases.
- `web` serves bundled framework-free assets and a protected loopback API.

## Runtime modes

Observe records calls and forwards them unchanged. Enforce evaluates each supported call; deny never
forwards, ask waits for one-time approval, and evaluation failure closes to deny. Replay is offline
and never starts an upstream process.

## Persistence

SQLite uses foreign keys, WAL mode, a busy timeout, and schema version 1. Runs own events; events own
approvals. Deleting a run cascades within the local database. Arguments are redacted before the
insert transaction. Tool results store only limited outcome metadata, not arbitrary result bodies.

Detailed design records and rationale live in [planning/ARCHITECTURE.md](../planning/ARCHITECTURE.md)
and [planning/adr/](../planning/adr/).
