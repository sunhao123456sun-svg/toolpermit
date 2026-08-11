# ToolPermit command patterns

Read this reference when exact commands or MCP client configuration are needed. Replace all
placeholders and resolve the ToolPermit executable to an absolute path before editing a client.

## Install and inspect

```bash
python -m venv .venv
.venv/bin/python -m pip install "toolpermit>=0.1,<0.2"
.venv/bin/toolpermit --version
.venv/bin/toolpermit init \
  --config .toolpermit/toolpermit.config.yaml \
  --policy .toolpermit/toolpermit.yaml
```

Windows PowerShell uses `.venv\Scripts\python.exe` and `.venv\Scripts\toolpermit.exe`.

## Wrap an MCP stdio server

Direct command:

```bash
/absolute/path/to/toolpermit wrap \
  --mode observe \
  --config /absolute/path/to/.toolpermit/toolpermit.config.yaml \
  -- \
  ORIGINAL_SERVER ORIGINAL_ARG_1 ORIGINAL_ARG_2
```

Generic MCP client JSON:

```json
{
  "command": "/absolute/path/to/toolpermit",
  "args": [
    "wrap",
    "--mode",
    "observe",
    "--config",
    "/absolute/path/to/.toolpermit/toolpermit.config.yaml",
    "--",
    "ORIGINAL_SERVER",
    "ORIGINAL_ARG_1"
  ]
}
```

Preserve any original `cwd` and environment variables in the client configuration. Do not put
secrets in ToolPermit policy or config files.

## Inspect, suggest, and replay

```bash
toolpermit runs list
toolpermit runs show RUN_ID --json
toolpermit audit export --run RUN_ID --format jsonl
toolpermit policy suggest --from-run RUN_ID --output candidate.yaml
toolpermit replay --policy candidate.yaml --baseline .toolpermit/toolpermit.yaml
```

For a CI-style regression signal, add `--json --fail-on-change` to `replay`.

## Enforce and decide

After policy review, replace only `observe` with `enforce` in the wrapper configuration.

```bash
toolpermit approvals list --json
toolpermit approvals approve APPROVAL_ID
toolpermit approvals reject APPROVAL_ID
toolpermit ui
```

Approval is one-time and request-bound. The UI must remain on the loopback URL printed by the CLI.

## Export, rollback, and delete

Rollback by restoring the original MCP server command and restarting the client. This bypasses
ToolPermit and does not remove audit records.

```bash
toolpermit audit export --run RUN_ID --output audit.jsonl
toolpermit audit delete RUN_ID --yes
```

Use the delete command only after the user explicitly confirms the exact run. ToolPermit cannot
recover deleted audit records.
