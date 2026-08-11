---
name: toolpermit
description: Install, configure, operate, and troubleshoot ToolPermit, the local-first permission policy, one-time approval, and redacted audit layer for MCP stdio tool calls. Use when Codex needs to protect or inspect an MCP server, wrap an MCP stdio command, create or review allow/ask/deny policies, manage approvals, replay recorded calls, export redacted audit data, or diagnose a ToolPermit setup. Do not use for remote MCP transports or as an operating-system sandbox.
---

# ToolPermit

Configure ToolPermit around a local MCP stdio server using an observe-first workflow. Keep every
policy decision reviewable and every state-changing step explicit.

## Operating contract

- Resolve bundled paths relative to this `SKILL.md`.
- Work in the user's selected project and prefer its existing Python environment.
- Never use `sudo`, modify a system Python, overwrite ToolPermit files, or edit an MCP client
  configuration without showing the intended change.
- Start in `observe` mode. Enter `enforce` mode only after the user reviews the policy and asks to
  enforce it.
- Never approve a pending tool call on the user's behalf unless they explicitly identify that exact
  approval and ask for approval. Rejection is always safe to offer.
- Treat `audit delete` as destructive. Require the run ID and explicit confirmation before using it.
- Explain that ToolPermit mediates calls routed through its stdio proxy; it is not an OS sandbox and
  cannot inspect bypass traffic or undo an executed action.

## Workflow

### 1. Inspect before changing anything

Identify:

1. The original MCP server executable and arguments.
2. The MCP client configuration file or UI that launches it.
3. The project Python environment and desired ToolPermit config directory.
4. Whether ToolPermit files or an existing wrapper already exist.

Run the bundled read-only doctor with the Python interpreter intended for ToolPermit:

```bash
python <skill-directory>/scripts/doctor.py --json
```

If ToolPermit is absent, propose a project virtual environment and install the compatible line with
`python -m pip install "toolpermit>=0.1,<0.2"`. Confirm before installing when the user only asked
for analysis or a plan. Verify with `toolpermit --version`.

### 2. Initialize safely

Choose explicit paths inside the project, then run `toolpermit init` only when neither target exists.
If files exist, read and validate them instead of passing `--force`. Keep the generated default
action as `ask` until observation evidence supports narrower rules.

Read [references/commands.md](references/commands.md) when exact CLI syntax, client JSON, Windows
paths, or lifecycle commands are needed.

### 3. Wrap the exact stdio command in observe mode

Resolve the absolute ToolPermit executable path from the selected environment. Preserve the original
server command and arguments after `--`. Present the resulting MCP client configuration as a diff or
complete replacement block and obtain confirmation before writing it.

Use `--mode observe` first. State clearly that observe mode records and forwards calls; it does not
enforce policy.

### 4. Verify a contained interaction

Restart or reconnect the MCP client, then exercise discovery or a harmless call chosen by the user.
Check `toolpermit runs list` and inspect the selected run. Confirm that expected calls appear and
that sensitive values are redacted before continuing.

If the server fails to start, preserve the original command and diagnose executable paths, working
directory, environment variables, config paths, and JSON quoting in that order.

### 5. Propose policy from evidence

Generate an inactive candidate with `policy suggest`. Review every generated `allow` rule, narrow
arguments or paths where possible, and retain `ask` or `deny` for uncertain actions. Replay the
candidate against stored calls. Treat indeterminate results caused by redaction as unresolved, never
as permission.

Do not replace the active policy automatically. Show the candidate and replay result before asking
whether to activate it.

### 6. Enforce only after review

After explicit approval, change the wrapper to `--mode enforce` with the reviewed policy. Exercise a
contained call and demonstrate one of these user-controlled approval paths:

- `toolpermit approvals list` followed by approval or rejection of one exact ID.
- `toolpermit ui`, using only the printed loopback URL.

Verify that denied or waiting calls did not reach the upstream server.

### 7. Hand off evidence and rollback

Report the files changed, exact wrapped command, active mode, policy path, database path, and
verification performed. Offer redacted JSONL export when durable evidence is useful. Provide the
original unwrapped MCP configuration as the rollback path; do not delete audit data during rollback.

## Completion criteria

Do not call setup complete until all applicable checks pass:

- Compatible Python and ToolPermit CLI verified.
- Existing files preserved or deliberate changes reviewed.
- Absolute wrapper executable and original stdio command confirmed.
- Observe-mode call recorded with expected redaction.
- Candidate policy replayed before enforcement.
- Enforce mode, if requested, tested with an exact approval or denial.
- User received rollback instructions and the documented limitations.
