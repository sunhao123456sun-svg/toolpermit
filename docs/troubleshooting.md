# Troubleshooting

## `configuration file not found`

An explicit `--config` path must exist. Run `toolpermit init --config PATH` or omit the flag to use
defaults. Relative database/policy paths resolve from the configuration file's directory.

## Policy fails before the server starts

This is fail-closed behavior. Check YAML indentation, `version: 1`, action spelling, unique rule IDs,
and unknown fields. Validate by running a replay against the file before enforce mode.

## Calls are not visible

Confirm the MCP client launches `toolpermit wrap ... -- ORIGINAL_COMMAND`, not the original server
directly. Check that the client uses `stdio`; v0.1 does not mediate Streamable HTTP. Observe mode
prints a warning but should still record supported `tools/call` requests.

## An asked call waits forever

Run `toolpermit approvals list` against the same database/configuration. Approve or reject the shown
ID, or launch `toolpermit ui`. Confirm both processes resolve the same database path. Pending and
approved records expire at their configured deadline.

## Approval is rejected as stale

The call may already be approved, rejected, cancelled, expired, executing, or completed. Approval is
single-use. List pending approvals again; do not retry an old ID.

## UI says `invalid Host header`

Open the exact URL printed by `toolpermit ui`. Do not use a LAN hostname, proxy, alternate port, or
manually changed Host header. Remote UI access is unsupported.

## UI mutation returns 403

Reload the exact local page so it obtains a fresh session and CSRF token. Cross-origin requests are
intentionally rejected. Extensions or proxies that rewrite Origin/Host may break the protection.

## Replay is `indeterminate`

A rule depends on a value that was irreversibly redacted. ToolPermit will not guess. Keep the result
gated, collect safe non-secret evidence, or revise the rule to use trustworthy non-secret fields.

## Database reports a newer schema

The database was opened by a newer ToolPermit version. Do not downgrade against the same file.
Restore a compatible backup or upgrade ToolPermit; never edit `PRAGMA user_version` manually.

## Upstream exits unexpectedly

Inspect the upstream server's stderr and command path. ToolPermit does not swallow server stderr.
Any approval that was executing during a ToolPermit restart is recovered as `unknown` and is not
automatically repeated.
