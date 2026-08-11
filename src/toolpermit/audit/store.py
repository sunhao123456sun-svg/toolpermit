"""SQLite event storage that enforces redaction before persistence."""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from toolpermit import __version__
from toolpermit.audit.migrations import MIGRATION_1, SCHEMA_VERSION
from toolpermit.domain.models import Decision, DecisionResult, ToolCall
from toolpermit.redaction import redact_with_report


class StorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunRecord:
    id: str
    mode: str
    started_at: float
    ended_at: float | None
    upstream_command: tuple[str, ...]


@dataclass(frozen=True)
class EventRecord:
    id: str
    run_id: str
    connection_id: str
    request_id: str | int
    occurred_at: float
    tool_name: str
    schema_fingerprint: str
    arguments: dict[str, Any]
    redacted_paths: tuple[str, ...]
    policy_digest: str
    rule_id: str
    decision: Decision
    explanation: str
    lifecycle: str
    outcome_metadata: dict[str, Any] | None
    upstream_duration_ms: float | None


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _as_object(value: str) -> object:
    return cast(object, json.loads(value))


def _as_dict(value: str) -> dict[str, Any]:
    parsed = _as_object(value)
    if not isinstance(parsed, dict):
        raise StorageError("stored JSON value is not an object")
    return cast(dict[str, Any], parsed)


def _as_string_tuple(value: str) -> tuple[str, ...]:
    parsed = _as_object(value)
    if not isinstance(parsed, list):
        raise StorageError("stored JSON value is not a string array")
    items = cast(list[object], parsed)
    if not all(isinstance(item, str) for item in items):
        raise StorageError("stored JSON value is not a string array")
    return tuple(cast(list[str], items))


class AuditStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            version_row = connection.execute("PRAGMA user_version").fetchone()
            if version_row is None:
                raise StorageError("cannot read SQLite schema version")
            version = cast(int, version_row[0])
            if version > SCHEMA_VERSION:
                raise StorageError(
                    f"database schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == 0:
                connection.executescript(MIGRATION_1)
                connection.execute(
                    "INSERT INTO metadata(key, value) VALUES ('application_version', ?)",
                    (__version__,),
                )
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def create_run(
        self,
        run_id: str,
        mode: str,
        upstream_command: Sequence[str],
        *,
        started_at: float | None = None,
    ) -> None:
        if mode not in {"observe", "enforce", "replay"}:
            raise ValueError(f"unsupported run mode: {mode}")
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?, NULL, ?)",
                (
                    run_id,
                    mode,
                    started_at if started_at is not None else time.time(),
                    _json(list(upstream_command)),
                ),
            )

    def finish_run(self, run_id: str, *, ended_at: float | None = None) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE runs SET ended_at = ? WHERE id = ? AND ended_at IS NULL",
                (ended_at if ended_at is not None else time.time(), run_id),
            )
            return cursor.rowcount == 1

    def record_event(
        self,
        call: ToolCall,
        result: DecisionResult,
        *,
        occurred_at: float | None = None,
        lifecycle: str = "decided",
    ) -> EventRecord:
        redacted, paths = redact_with_report(call.arguments)
        if not isinstance(redacted, dict):
            raise StorageError("tool arguments must remain an object after redaction")
        safe_arguments = cast(dict[str, Any], redacted)
        timestamp = occurred_at if occurred_at is not None else time.time()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO events (
                    id, run_id, connection_id, request_id_json, occurred_at,
                    tool_name, schema_fingerprint, arguments_json, redacted_paths_json,
                    policy_digest, rule_id, decision, explanation, lifecycle,
                    outcome_metadata_json, upstream_duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    call.event_id,
                    call.run_id,
                    call.connection_id,
                    _json(call.request_id),
                    timestamp,
                    call.tool_name,
                    call.schema_fingerprint,
                    _json(safe_arguments),
                    _json(paths),
                    result.policy_digest,
                    result.rule_id,
                    result.decision.value,
                    result.explanation,
                    lifecycle,
                ),
            )
        return self.get_event(call.event_id)

    def update_lifecycle(self, event_id: str, lifecycle: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE events SET lifecycle = ? WHERE id = ?",
                (lifecycle, event_id),
            )
            return cursor.rowcount == 1

    def record_outcome(
        self,
        event_id: str,
        *,
        is_error: bool,
        content_types: Sequence[str],
        duration_ms: float,
        lifecycle: str,
    ) -> bool:
        metadata = {"is_error": is_error, "content_types": sorted(set(content_types))}
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE events
                SET outcome_metadata_json = ?, upstream_duration_ms = ?, lifecycle = ?
                WHERE id = ?
                """,
                (_json(metadata), duration_ms, lifecycle, event_id),
            )
            return cursor.rowcount == 1

    def get_event(self, event_id: str) -> EventRecord:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise KeyError(event_id)
        return self._event_from_row(row)

    def list_events(self, *, run_id: str | None = None) -> tuple[EventRecord, ...]:
        query = "SELECT * FROM events"
        parameters: tuple[object, ...] = ()
        if run_id is not None:
            query += " WHERE run_id = ?"
            parameters = (run_id,)
        query += " ORDER BY occurred_at, id"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(self._event_from_row(row) for row in rows)

    def list_runs(self) -> tuple[RunRecord, ...]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY started_at DESC, id").fetchall()
        return tuple(self._run_from_row(row) for row in rows)

    def export_jsonl(self, *, run_id: str | None = None) -> Iterator[str]:
        for event in self.list_events(run_id=run_id):
            yield _json(
                {
                    "schema_version": 1,
                    "event_id": event.id,
                    "run_id": event.run_id,
                    "connection_id": event.connection_id,
                    "request_id": event.request_id,
                    "occurred_at": event.occurred_at,
                    "tool_name": event.tool_name,
                    "schema_fingerprint": event.schema_fingerprint,
                    "arguments": event.arguments,
                    "redacted_paths": list(event.redacted_paths),
                    "policy_digest": event.policy_digest,
                    "rule_id": event.rule_id,
                    "decision": event.decision.value,
                    "explanation": event.explanation,
                    "lifecycle": event.lifecycle,
                    "outcome_metadata": event.outcome_metadata,
                    "upstream_duration_ms": event.upstream_duration_ms,
                }
            )

    def delete_run(self, run_id: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            return cursor.rowcount == 1

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> EventRecord:
        request_id = _as_object(cast(str, row["request_id_json"]))
        if not isinstance(request_id, (str, int)) or isinstance(request_id, bool):
            raise StorageError("stored request ID is invalid")
        outcome_raw = cast(str | None, row["outcome_metadata_json"])
        return EventRecord(
            id=cast(str, row["id"]),
            run_id=cast(str, row["run_id"]),
            connection_id=cast(str, row["connection_id"]),
            request_id=request_id,
            occurred_at=cast(float, row["occurred_at"]),
            tool_name=cast(str, row["tool_name"]),
            schema_fingerprint=cast(str, row["schema_fingerprint"]),
            arguments=_as_dict(cast(str, row["arguments_json"])),
            redacted_paths=_as_string_tuple(cast(str, row["redacted_paths_json"])),
            policy_digest=cast(str, row["policy_digest"]),
            rule_id=cast(str, row["rule_id"]),
            decision=Decision(cast(str, row["decision"])),
            explanation=cast(str, row["explanation"]),
            lifecycle=cast(str, row["lifecycle"]),
            outcome_metadata=_as_dict(outcome_raw) if outcome_raw is not None else None,
            upstream_duration_ms=cast(float | None, row["upstream_duration_ms"]),
        )

    @staticmethod
    def _run_from_row(row: sqlite3.Row) -> RunRecord:
        command = _as_string_tuple(cast(str, row["upstream_command_json"]))
        return RunRecord(
            id=cast(str, row["id"]),
            mode=cast(str, row["mode"]),
            started_at=cast(float, row["started_at"]),
            ended_at=cast(float | None, row["ended_at"]),
            upstream_command=command,
        )
