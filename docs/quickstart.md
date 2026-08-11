# Quickstart

This walkthrough uses no API key and writes only to a disposable directory you choose. It covers
observe, inspect, suggest, replay, enforce, approve, export, and delete.

## 1. Install the release in a checkout

ToolPermit requires Python 3.11–3.13.

```bash
python -m venv .venv
.venv/bin/python -m pip install "toolpermit==0.1.0"
.venv/bin/toolpermit --version
.venv/bin/toolpermit init
```

On Windows PowerShell, replace `.venv/bin/` with `.venv\Scripts\` and use `mkdir
demo-workspace` as usual. `init` creates:

- `toolpermit.config.yaml`: local database, policy, approval lifetime, and UI address.
- `toolpermit.yaml`: a safe starter policy whose default action is `ask`.

The command refuses to overwrite either file unless `--force` is explicit.

## 2. Observe a contained call

```bash
mkdir demo-workspace
.venv/bin/python examples/demo_client.py \
  --mode observe \
  --demo-dir demo-workspace
```

The client starts `examples/demo_server.py` through ToolPermit, discovers its tools, and requests a
write to `demo-workspace/output.txt`. Observe mode forwards the call and records a redacted event;
it does not enforce policy. The warning on stderr is intentional.

```bash
.venv/bin/toolpermit runs list
.venv/bin/toolpermit runs show RUN_ID
.venv/bin/toolpermit audit export --run RUN_ID --format jsonl
```

Copy the run ID shown by `runs list` into the following commands.

## 3. Suggest and replay a policy

```bash
.venv/bin/toolpermit policy suggest \
  --from-run RUN_ID \
  --output candidate.yaml
.venv/bin/toolpermit replay \
  --policy candidate.yaml \
  --baseline toolpermit.yaml
```

The candidate is marked inactive. ToolPermit never replaces the active policy automatically. Read
every generated `allow` rule, narrow it if needed, and pay attention to `indeterminate` replay
results caused by irreversible redaction. For CI, add `--json --fail-on-change`.

## 4. Require one-time approval

The starter policy uses `default: ask`. In terminal A:

```bash
.venv/bin/python examples/demo_client.py \
  --mode enforce \
  --policy toolpermit.yaml \
  --demo-dir demo-workspace
```

The client waits before the write. In terminal B, either use the CLI:

```bash
.venv/bin/toolpermit approvals list
.venv/bin/toolpermit approvals approve APPROVAL_ID
```

or launch the web UI:

```bash
.venv/bin/toolpermit ui
```

Open exactly the printed loopback URL. Approval is one-time and bound to the canonical call. A
changed argument creates a different request and cannot reuse the approval. Use `approvals reject`
to deny instead.

## 5. Inspect and clean up

```bash
.venv/bin/toolpermit runs list
.venv/bin/toolpermit runs show RUN_ID --json
.venv/bin/toolpermit audit export --run RUN_ID --output audit.jsonl
.venv/bin/toolpermit audit delete RUN_ID --yes
```

`audit delete` permanently removes the selected run, its events, and associated approvals from the
ToolPermit database. Remove `demo-workspace`, `candidate.yaml`, and `audit.jsonl` when finished.

## Next steps

- Learn precise matching rules in [Policy reference](policy-reference.md).
- Configure a real MCP client using [CLI reference](cli-reference.md#wrap).
- Read [Security](security.md) and [Known limitations](limitations.md) before enforcement.
