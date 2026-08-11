# Known limitations

The following are intentional v0.1 boundaries, not hidden roadmap promises.

- Only local MCP `stdio` is supported. Streamable HTTP and remote transports are not mediated.
- The deployment model is one local user; there are no accounts, teams, RBAC, or remote approvers.
- The web UI is loopback-only and must not be reverse-proxied or exposed on a network.
- ToolPermit is not an OS sandbox and cannot prevent calls that bypass its wrapper.
- Path matching is deterministic policy input matching, not a defense against every symlink, mount,
  or TOCTOU race in an upstream tool.
- Redaction is irreversible and intentionally reduces replay precision; affected matches become
  indeterminate.
- Policy suggestions use observed redacted evidence and can be overly broad. They are inactive until
  manually selected.
- Stored tool outcomes contain limited metadata, not full result bodies.
- Database retention is manual; there is no scheduler or automatic expiry of old runs.
- Human CLI wording and visual design may change during `0.x`; versioned JSON/schema contracts are
  the automation surface.
- No container image, hosted service, telemetry, model-based policy, or automatic update checker is
  included.

See [ROADMAP.md](../ROADMAP.md) for candidates that may be evaluated after v0.1.
