"""Monotonic SQLite schema migrations."""

SCHEMA_VERSION = 1

MIGRATION_1 = """
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    mode TEXT NOT NULL CHECK (mode IN ('observe', 'enforce', 'replay')),
    started_at REAL NOT NULL,
    ended_at REAL,
    upstream_command_json TEXT NOT NULL
);

CREATE TABLE events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    connection_id TEXT NOT NULL,
    request_id_json TEXT NOT NULL,
    occurred_at REAL NOT NULL,
    tool_name TEXT NOT NULL,
    schema_fingerprint TEXT NOT NULL,
    arguments_json TEXT NOT NULL,
    redacted_paths_json TEXT NOT NULL,
    policy_digest TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('allow', 'ask', 'deny')),
    explanation TEXT NOT NULL,
    lifecycle TEXT NOT NULL,
    outcome_metadata_json TEXT,
    upstream_duration_ms REAL
);

CREATE INDEX events_run_time ON events(run_id, occurred_at, id);
CREATE INDEX events_tool ON events(tool_name, schema_fingerprint);
CREATE INDEX events_decision ON events(decision);

CREATE TABLE approvals (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    request_digest TEXT NOT NULL,
    state TEXT NOT NULL CHECK (
        state IN ('pending', 'approved', 'rejected', 'expired', 'cancelled',
                  'executing', 'executed', 'failed', 'unknown')
    ),
    expires_at REAL NOT NULL,
    actor TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    error TEXT
);

CREATE INDEX approvals_state_expiry ON approvals(state, expires_at);
"""

