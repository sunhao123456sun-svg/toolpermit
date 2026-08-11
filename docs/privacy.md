# Privacy and data lifecycle

ToolPermit is local-first and has no telemetry in v0.1. It does not send audit records to a cloud
service or call a model API.

## Stored data

The SQLite database stores run IDs/mode/timestamps/upstream command, connection and request IDs,
tool name, input-schema fingerprint, redacted arguments and redacted paths, policy/rule decision and
explanation, lifecycle, limited outcome metadata, durations, and approval state/timestamps/actor.

Arbitrary upstream result bodies are not stored. Values recognized as credentials or under
sensitive keys are replaced with a structured sentinel before persistence. Originals cannot be
revealed because they are not retained.

## Location and retention

The default database is `.toolpermit/audit.db` relative to the configuration directory. ToolPermit
does not delete old runs automatically in v0.1; the operator controls retention.

```bash
toolpermit runs list
toolpermit audit export --run RUN_ID --output audit.jsonl
toolpermit audit delete RUN_ID --yes
```

Deletion removes the selected run and cascades to its events and approvals in the active database.
It does not erase copies in filesystem backups, exported files, snapshots, or forensic storage.

## Safe sharing

Exports are redacted again by construction, but metadata such as tool names, paths not classified as
sensitive, commands, timestamps, and explanations may still be confidential. Review an export
before sharing. Never upload the raw SQLite database to a public issue.
