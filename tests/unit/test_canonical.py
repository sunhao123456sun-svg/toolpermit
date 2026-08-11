from __future__ import annotations

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from toolpermit.canonical import approval_digest, canonical_bytes, schema_fingerprint

JSON_SCALAR = (
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text()
)
JSON_VALUE = st.recursive(
    JSON_SCALAR,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(st.text(max_size=20), children, max_size=5),
    max_leaves=20,
)


@given(st.dictionaries(st.text(max_size=20), JSON_VALUE, max_size=8))
def test_canonical_mapping_is_independent_of_insertion_order(value: dict[str, object]) -> None:
    assert canonical_bytes(value) == canonical_bytes(dict(reversed(list(value.items()))))


def test_canonical_encoding_preserves_string_and_numeric_types() -> None:
    assert canonical_bytes("é") != canonical_bytes("e\u0301")
    assert canonical_bytes(1) != canonical_bytes(1.0)
    assert canonical_bytes(0.0) != canonical_bytes(-0.0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(value: float) -> None:
    with pytest.raises(ValueError):
        canonical_bytes({"value": value})


def test_approval_digest_binds_every_security_field() -> None:
    base = {
        "tool_name": "filesystem.write_file",
        "schema_fingerprint_value": "a" * 64,
        "arguments": {"path": "notes.txt", "content": "hello"},
        "run_id": "run-1",
        "connection_id": "connection-1",
        "policy_digest_value": "b" * 64,
        "expires_at": 1_800_000_000.0,
    }
    original = approval_digest(**base)
    replacements = {
        "tool_name": "filesystem.delete_file",
        "schema_fingerprint_value": "c" * 64,
        "arguments": {"path": "other.txt", "content": "hello"},
        "run_id": "run-2",
        "connection_id": "connection-2",
        "policy_digest_value": "d" * 64,
        "expires_at": 1_800_000_001.0,
    }
    for key, replacement in replacements.items():
        changed = json.loads(json.dumps(base))
        changed[key] = replacement
        assert approval_digest(**changed) != original


def test_schema_fingerprint_is_stable() -> None:
    schema = {"type": "object", "properties": {"text": {"type": "string"}}}
    assert schema_fingerprint(schema) == schema_fingerprint(dict(reversed(list(schema.items()))))
