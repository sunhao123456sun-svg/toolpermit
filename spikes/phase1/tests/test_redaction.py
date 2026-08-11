from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from spikes.phase1.redaction import REDACTED, redact


def test_redacts_keys_and_embedded_secret_shapes() -> None:
    raw = {
        "api_key": "sk-abcdefghijklmnopqrstuvwxyz",
        "nested": {"message": "Authorization: Bearer very-secret-value"},
        "safe": ["hello", 3],
    }
    result = redact(raw)
    serialized = json.dumps(result)
    assert "abcdefghijklmnopqrstuvwxyz" not in serialized
    assert "very-secret-value" not in serialized
    assert result["api_key"] == REDACTED
    assert result["safe"] == ["hello", 3]


def test_raw_secret_never_reaches_sqlite(tmp_path: Path) -> None:
    secret = "sk-this-secret-must-never-persist"
    redacted = redact({"token": secret, "path": "notes.txt"})
    database = tmp_path / "events.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE events (payload TEXT NOT NULL)")
    connection.execute("INSERT INTO events VALUES (?)", (json.dumps(redacted),))
    connection.commit()
    connection.close()

    assert secret.encode() not in database.read_bytes()

