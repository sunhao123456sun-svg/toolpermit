# Policy reference

Policy schema version 1 is strict YAML. Unknown fields, duplicate rule IDs, invalid actions, and
unsupported versions prevent enforcement from starting.

## Document shape

```yaml
version: 1
default: ask
rules:
  - id: stable-human-readable-id
    action: allow
    explanation: Why this exact call is expected.
    match:
      tool: filesystem.read_file
      arguments:
        path:
          path_under: /safe/project
```

`version` and `default` are required. `rules` defaults to an empty list. Actions are `allow`, `ask`,
or `deny`.

## Precedence

Rules are evaluated from top to bottom. The first matching rule wins. If none matches, `default`
wins. Put narrow exceptions before broad rules. ToolPermit does not calculate “most specific” and
does not merge multiple matches.

Every decision records the winning rule ID (or `$default`), explanation, and policy digest.

## Tool matching

`match.tool` is an exact, case-sensitive tool name. Omitting it matches any tool and should be used
sparingly. There is no regex or fuzzy tool-name matching in v0.1.

## Argument conditions

Each configured argument condition must match. Missing arguments do not match.

### Exact

```yaml
arguments:
  branch:
    exact: main
  dry_run:
    exact: true
```

Exact matching is type-sensitive: the string `"1"` is different from integer `1`, and boolean
`true` is not integer `1`.

### Glob

```yaml
arguments:
  filename:
    glob: "reports/*.md"
```

Glob matching applies to a string value using deterministic path-style wildcards. It is a string
constraint, not a filesystem authorization check.

### Path under

```yaml
arguments:
  path:
    path_under: /absolute/approved/root
```

`path_under` normalizes lexical path components and requires the value to remain under the stated
root. It does not turn ToolPermit into an OS sandbox. A malicious server, symlink change, mount
change, or check/use race can still change what an upstream tool accesses. Prefer a real sandbox
when filesystem containment is a security boundary.

## Canonicalization and approvals

ToolPermit uses a typed, versioned canonical encoding (`TP-CANONICAL-V1`) so values such as strings,
numbers, booleans, arrays, and objects cannot collide through ordinary JSON formatting differences.
The one-time approval digest binds:

- tool name and input-schema fingerprint;
- complete normalized arguments;
- run and connection IDs;
- policy digest; and
- approval expiry.

Changing any bound field produces a different digest. Atomic state transitions ensure that only one
consumer can move an approved request to execution.

## Redacted replay

Sensitive values are never retained. When a candidate rule depends on a redacted field, replay
reports `indeterminate` rather than guessing. A policy suggestion omits redacted scalar constraints
and warns when the remaining rule is broad.

## Recommended pattern

Start with `default: ask` or `default: deny`. Observe representative local traffic, generate an
inactive candidate, review every `allow`, replay it against history, and keep destructive tools at
`ask` until their true boundary is understood.
