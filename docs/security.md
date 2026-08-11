# Security model

## What ToolPermit protects

For supported MCP `stdio` tool calls that pass through its proxy, ToolPermit can apply deterministic
policy, stop denied calls before upstream execution, suspend asked calls for exact one-time approval,
record redacted evidence, and expose policy changes through offline replay.

## What it does not protect

ToolPermit is not a process, filesystem, network, container, or operating-system sandbox. It cannot
mediate a client configured to call the upstream server directly, code executed outside MCP,
unsupported transports, or side effects already performed. Policy permission is not proof that the
upstream implementation is honest or race-free.

## Important controls

- Enforcement requires a valid policy and fails closed on evaluation errors.
- Typed canonicalization and schema fingerprints prevent approval substitution through formatting or
  type ambiguity.
- Approval transitions are conditional SQLite updates; approval is time-bounded and single-use.
- Cancellation before execution never forwards the tool call.
- In-flight approvals become `unknown` after restart instead of being retried automatically.
- Redaction occurs before database persistence, UI rendering, and export.
- The UI accepts loopback binding only, exact Host and same-origin mutation requests, a per-session
  CSRF token, SameSite/HttpOnly cookies, restrictive CSP, escaped DOM text, and no permissive CORS.

## Operator responsibilities

1. Replace the real MCP server command with the ToolPermit wrapper in every intended client.
2. Keep the local account, policy, configuration, and SQLite file protected by normal OS controls.
3. Review tool semantics and arguments, not only the tool name.
4. Use an OS sandbox when path/network/process containment matters.
5. Treat `unknown`, replay `indeterminate`, broad generated rules, and observe mode warnings as
   unresolved risk—not as approval.

## Browser boundary

The UI deliberately has no remote mode in v0.1. Do not place it behind a reverse proxy or expose the
port on a LAN. A compromised browser profile or malicious local process remains within the local
account threat boundary.

## Reporting

Follow [SECURITY.md](../SECURITY.md) for private reporting. The implementation-oriented threat model
is [planning/THREAT_MODEL.md](../planning/THREAT_MODEL.md).
