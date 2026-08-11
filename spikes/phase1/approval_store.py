"""SQLite approval lifecycle spike."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    state TEXT NOT NULL CHECK (
        state IN ('pending', 'approved', 'rejected', 'expired', 'cancelled',
                  'executing', 'executed', 'failed', 'unknown')
    ),
    expires_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""


class ApprovalStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def create(self, approval_id: str, request_digest: str, expires_at: float) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO approvals VALUES (?, ?, 'pending', ?, ?)",
                (approval_id, request_digest, expires_at, time.time()),
            )

    def approve(self, approval_id: str) -> bool:
        now = time.time()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals
                SET state = 'approved', updated_at = ?
                WHERE id = ? AND state = 'pending' AND expires_at > ?
                """,
                (now, approval_id, now),
            )
            return cursor.rowcount == 1

    def consume(self, approval_id: str, request_digest: str) -> bool:
        now = time.time()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals
                SET state = 'executing', updated_at = ?
                WHERE id = ? AND request_digest = ? AND state = 'approved'
                  AND expires_at > ?
                """,
                (now, approval_id, request_digest, now),
            )
            return cursor.rowcount == 1

    def recover_inflight(self) -> int:
        """Mark uncertain executions without retrying their side effect."""

        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE approvals SET state = 'unknown', updated_at = ?
                WHERE state = 'executing'
                """,
                (time.time(),),
            )
            return cursor.rowcount

    def state(self, approval_id: str) -> str:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT state FROM approvals WHERE id = ?", (approval_id,)
            ).fetchone()
        if row is None:
            raise KeyError(approval_id)
        return str(row[0])

