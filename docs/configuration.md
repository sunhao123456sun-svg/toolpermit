# Configuration

ToolPermit uses one strict YAML configuration file. The default name is
`toolpermit.config.yaml`; pass `--config PATH` to select another file. Unknown fields and unsupported
versions fail validation.

```yaml
version: 1
database: .toolpermit/audit.db
policy: toolpermit.yaml
approval_ttl: 300
ui:
  host: 127.0.0.1
  port: 8765
```

| Field | Meaning |
| --- | --- |
| `version` | Required configuration schema version; v0.1 accepts only `1`. |
| `database` | SQLite audit/approval path. Relative paths resolve from the configuration directory. |
| `policy` | Active enforce-mode policy path, resolved from the configuration directory. |
| `approval_ttl` | Approval lifetime in seconds; greater than 0 and at most 86,400. |
| `ui.host` | `127.0.0.1`, `localhost`, or `::1` only. |
| `ui.port` | TCP port from 1 to 65,535. |

Explicit command options such as `--database`, `--policy`, `--approval-ttl`, `--host`, and `--port`
override the corresponding effective value for that invocation. v0.1 defines no configuration
environment-variable overrides and stores no secrets in this file. The contained demo uses a
separate `TOOLPERMIT_DEMO_DIR` variable only to bound its fixture server.

Run `toolpermit config show --json` to inspect resolved non-secret settings. ToolPermit never sends
effective configuration or audit data as telemetry.
