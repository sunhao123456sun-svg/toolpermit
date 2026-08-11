"""Spike for canonical approval request serialization and digests."""

from __future__ import annotations

import hashlib
import json
from typing import Any

DOMAIN = b"toolpermit-approval-v1\x00"


def canonical_json(value: Any) -> bytes:
    """Serialize JSON data deterministically for the spike.

    Strings are preserved exactly: Unicode normalization is deliberately not
    performed because it could change an upstream tool argument.
    """

    text = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return text.encode("utf-8")


def approval_digest(
    *,
    tool_name: str,
    schema_fingerprint: str,
    arguments: dict[str, Any],
    run_id: str,
    policy_digest: str,
) -> str:
    request = {
        "arguments": arguments,
        "policy_digest": policy_digest,
        "run_id": run_id,
        "schema_fingerprint": schema_fingerprint,
        "tool_name": tool_name,
        "version": 1,
    }
    return hashlib.sha256(DOMAIN + canonical_json(request)).hexdigest()

