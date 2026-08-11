"""TP-CANONICAL-V1 serialization and security-relevant digests."""

from __future__ import annotations

import hashlib
import math
import struct
from collections.abc import Mapping, Sequence
from typing import Any, cast

ENCODING_PREFIX = b"TP-CANONICAL-V1\x00"
APPROVAL_DOMAIN = b"toolpermit/approval/v1\x00"
POLICY_DOMAIN = b"toolpermit/policy/v1\x00"
SCHEMA_DOMAIN = b"toolpermit/schema/v1\x00"


def _length(value: int) -> bytes:
    if value < 0 or value >= 2**64:
        raise ValueError("canonical length is outside uint64 range")
    return struct.pack(">Q", value)


def _encode(value: Any) -> bytes:
    if value is None:
        return b"n"
    if value is False:
        return b"f"
    if value is True:
        return b"t"
    if isinstance(value, int):
        magnitude = str(abs(value)).encode("ascii")
        sign = b"-" if value < 0 else b"+"
        return b"i" + sign + _length(len(magnitude)) + magnitude
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite floats are not canonical JSON values")
        return b"d" + struct.pack(">d", value)
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + _length(len(encoded)) + encoded
    if isinstance(value, Mapping):
        items: list[tuple[bytes, Any]] = []
        mapping = cast(Mapping[object, object], value)
        for key, item in mapping.items():
            if not isinstance(key, str):
                raise TypeError("canonical object keys must be strings")
            items.append((key.encode("utf-8"), item))
        items.sort(key=lambda pair: pair[0])
        payload = bytearray(b"o" + _length(len(items)))
        for key_bytes, item in items:
            payload.extend(b"s" + _length(len(key_bytes)) + key_bytes)
            payload.extend(_encode(item))
        return bytes(payload)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        sequence = cast(Sequence[object], value)
        payload = bytearray(b"a" + _length(len(sequence)))
        for item in sequence:
            payload.extend(_encode(item))
        return bytes(payload)
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Encode a JSON-compatible value without Unicode or numeric coercion."""

    return ENCODING_PREFIX + _encode(value)


def domain_digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + canonical_bytes(value)).hexdigest()


def policy_digest(policy_data: Mapping[str, Any]) -> str:
    return domain_digest(POLICY_DOMAIN, policy_data)


def schema_fingerprint(schema: Mapping[str, Any]) -> str:
    return domain_digest(SCHEMA_DOMAIN, schema)


def approval_digest(
    *,
    tool_name: str,
    schema_fingerprint_value: str,
    arguments: Mapping[str, Any],
    run_id: str,
    connection_id: str,
    policy_digest_value: str,
    expires_at: float,
) -> str:
    request = {
        "arguments": dict(arguments),
        "connection_id": connection_id,
        "expires_at": expires_at,
        "policy_digest": policy_digest_value,
        "purpose": "execute-tool-call",
        "run_id": run_id,
        "schema_fingerprint": schema_fingerprint_value,
        "tool_name": tool_name,
        "version": 1,
    }
    return domain_digest(APPROVAL_DOMAIN, request)
