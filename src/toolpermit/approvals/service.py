"""Race-safe, single-use approval transitions in SQLite."""

from __future__ import annotations

import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import cast

from toolpermit.audit.store import AuditStore
from toolpermit.canonical import approval_digest
from toolpermit.domain.models import ApprovalState, ToolCall


@dataclass(frozen=True)
class ApprovalRecord:
    id: str
    event_id: str
    request_digest: str
    state: ApprovalState
    expires_at: float
    actor: str | None
    created_at: float
    updated_at: float
    error: str | None


class ApprovalService:
    def __init__(self, store: AuditStore) -> None:
        self.store = store

    def create_pending(
        self,
        event_id: str,
        call: ToolCall,
        policy_digest: str,
        expires_at: float,
        *,
        approval_id: str | None = None,
        now: float | None = None,
    ) -> ApprovalRecord:
        timestamp = now if now is not None else time.time()
        if expires_at <= timestamp:
            raise ValueError("approval expiry must be in the future")
        identifier = approval_id or f"apr_{uuid.uuid4().hex}"
        digest = approval_digest(
            tool_name=call.tool_name,
            schema_fingerprint_value=call.schema_fingerprint,
            arguments=call.arguments,
            run_id=call.run_id,
            connection_id=call.connection_id,
            policy_digest_value=policy_digest,
            expires_at=expires_at,
        )
        with self.store.connect() as connection:
            connection.execute(
                "INSERT INTO approvals VALUES (?, ?, ?, 'pending', ?, NULL, ?, ?, NULL)",
                (identifier, event_id, digest, expires_at, timestamp, timestamp),
            )
        return self.get(identifier)

    def get(self, approval_id: str) -> ApprovalRecord:
        with self.store.connect() as connection:
            row = connection.execute(
                "SELECT * FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        if row is None:
            raise KeyError(approval_id)
        return self._from_row(row)

    def list_pending(self, *, now: float | None = None) -> tuple[ApprovalRecord, ...]:
        self.expire_due(now=now)
        with self.store.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM approvals WHERE state = 'pending' ORDER BY created_at, id"
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def approve(self, approval_id: str, *, actor: str = "local", now: float | None = None) -> bool:
        timestamp = now if now is not None else time.time()
        with self.store.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = 'approved', actor = ?, updated_at = ?
                WHERE id = ? AND state = 'pending' AND expires_at > ?
                """,
                (actor, timestamp, approval_id, timestamp),
            )
            return cursor.rowcount == 1

    def reject(self, approval_id: str, *, actor: str = "local", now: float | None = None) -> bool:
        return self._terminal_before_execution(
            approval_id, ApprovalState.REJECTED, actor=actor, now=now
        )

    def cancel(self, approval_id: str, *, actor: str = "client", now: float | None = None) -> bool:
        return self._terminal_before_execution(
            approval_id, ApprovalState.CANCELLED, actor=actor, now=now
        )

    def expire_due(self, *, now: float | None = None) -> int:
        timestamp = now if now is not None else time.time()
        with self.store.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = 'expired', updated_at = ?
                WHERE state IN ('pending', 'approved') AND expires_at <= ?
                """,
                (timestamp, timestamp),
            )
            return cursor.rowcount

    def consume(
        self,
        approval_id: str,
        expected_digest: str,
        *,
        now: float | None = None,
    ) -> bool:
        timestamp = now if now is not None else time.time()
        with self.store.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = 'executing', updated_at = ?
                WHERE id = ? AND request_digest = ? AND state = 'approved'
                  AND expires_at > ?
                """,
                (timestamp, approval_id, expected_digest, timestamp),
            )
            return cursor.rowcount == 1

    def mark_executed(self, approval_id: str, *, now: float | None = None) -> bool:
        return self._finish_execution(approval_id, ApprovalState.EXECUTED, None, now=now)

    def mark_failed(
        self,
        approval_id: str,
        error: str,
        *,
        now: float | None = None,
    ) -> bool:
        return self._finish_execution(approval_id, ApprovalState.FAILED, error, now=now)

    def recover_inflight(self, *, now: float | None = None) -> int:
        timestamp = now if now is not None else time.time()
        with self.store.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = 'unknown', updated_at = ?,
                    error = 'process restarted during execution'
                WHERE state = 'executing'
                """,
                (timestamp,),
            )
            return cursor.rowcount

    def _terminal_before_execution(
        self,
        approval_id: str,
        target: ApprovalState,
        *,
        actor: str,
        now: float | None,
    ) -> bool:
        if target not in {ApprovalState.REJECTED, ApprovalState.CANCELLED}:
            raise ValueError("invalid pre-execution terminal state")
        timestamp = now if now is not None else time.time()
        with self.store.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = ?, actor = ?, updated_at = ?
                WHERE id = ? AND state IN ('pending', 'approved')
                """,
                (target.value, actor, timestamp, approval_id),
            )
            return cursor.rowcount == 1

    def _finish_execution(
        self,
        approval_id: str,
        target: ApprovalState,
        error: str | None,
        *,
        now: float | None,
    ) -> bool:
        if target not in {ApprovalState.EXECUTED, ApprovalState.FAILED}:
            raise ValueError("invalid execution terminal state")
        timestamp = now if now is not None else time.time()
        with self.store.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = ?, updated_at = ?, error = ?
                WHERE id = ? AND state = 'executing'
                """,
                (target.value, timestamp, error, approval_id),
            )
            return cursor.rowcount == 1

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ApprovalRecord:
        return ApprovalRecord(
            id=cast(str, row["id"]),
            event_id=cast(str, row["event_id"]),
            request_digest=cast(str, row["request_digest"]),
            state=ApprovalState(cast(str, row["state"])),
            expires_at=cast(float, row["expires_at"]),
            actor=cast(str | None, row["actor"]),
            created_at=cast(float, row["created_at"]),
            updated_at=cast(float, row["updated_at"]),
            error=cast(str | None, row["error"]),
        )

