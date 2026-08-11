# CLI reference

Human-readable output may improve during `0.x`. Output produced by `--json` includes a
`schema_version` and is the intended automation interface.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success. |
| 2 | Typer/Click command-line usage error. |
| 3 | Invalid configuration, policy, mode, or unsupported format. |
| 4 | Conflict, missing record, stale approval, or refused overwrite/deletion. |
| 5 | Replay regression threshold failed. |

## `init`

```bash
toolpermit init [--config PATH] [--policy PATH] [--force]
```

Creates one strict configuration and one approval-first policy. It checks both targets before
writing, so a normal invocation cannot partially overwrite an existing project.

## `wrap`

```bash
toolpermit wrap --mode observe -- COMMAND [ARG ...]
toolpermit wrap --mode enforce --policy POLICY -- COMMAND [ARG ...]
```

`COMMAND` must be an MCP `stdio` server. Put `--` before the upstream command so its flags are not
parsed by ToolPermit. `observe` records and forwards; it never enforces. `enforce` requires a valid
policy and fails before starting the server if loading fails.

Options include `--config`, `--database`, and `--approval-ttl`. Explicit flags override values from
the selected configuration. ToolPermit must replace the MCP server command in the client's
configuration; calls sent directly to the original command bypass mediation.

## `policy suggest`

```bash
toolpermit policy suggest --from-run RUN_ID --output PATH [--force]
```

Writes a deterministic inactive candidate using redacted evidence from one run. It never edits the
configured active policy.

## `replay`

```bash
toolpermit replay --policy POLICY [--baseline POLICY] [--run RUN_ID]
                  [--json] [--fail-on-change]
```

Evaluates stored calls without starting an upstream server. `--fail-on-change` exits 5 for a
transition other than `unchanged`/initial `evaluated`, including an indeterminate comparison.

## `approvals`

```bash
toolpermit approvals list [--json]
toolpermit approvals approve APPROVAL_ID
toolpermit approvals reject APPROVAL_ID
```

Only pending approvals are listed. Approve/reject operations use the same atomic application
service as the web UI. A stale, expired, already-used, or unknown ID exits 4.

## `runs`

```bash
toolpermit runs list [--json]
toolpermit runs show RUN_ID [--json]
```

Shows local run metadata and redacted event details.

## `audit`

```bash
toolpermit audit export [--run RUN_ID] [--format jsonl] [--output PATH]
toolpermit audit delete RUN_ID --yes
```

JSONL export is deterministic and versioned. Deletion is permanent within ToolPermit and cascades
to events and approvals; it requires `--yes`.

## `config show`

```bash
toolpermit config show [--config PATH] [--json]
```

Displays resolved paths and effective non-secret settings. Unknown configuration fields are fatal.

## `ui`

```bash
toolpermit ui [--host 127.0.0.1] [--port 8765]
```

Serves the bundled local interface. v0.1 accepts only `127.0.0.1`, `localhost`, or `::1`; a
non-loopback address is rejected rather than exposed with a warning.
