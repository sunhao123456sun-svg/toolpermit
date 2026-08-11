from __future__ import annotations

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from spikes.phase1.canonical import approval_digest, canonical_json

JSON_SCALAR = st.none() | st.booleans() | st.integers() | st.text()
JSON_VALUE = st.recursive(
    JSON_SCALAR,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(st.text(max_size=20), children, max_size=5),
    max_leaves=20,
)


@given(st.dictionaries(st.text(max_size=20), JSON_VALUE, max_size=8))
def test_canonical_json_is_independent_of_dict_insertion_order(value: dict[str, object]) -> None:
    reversed_value = dict(reversed(list(value.items())))
    assert canonical_json(value) == canonical_json(reversed_value)


def test_canonical_json_preserves_strings_without_unicode_normalization() -> None:
    assert canonical_json({"value": "é"}) != canonical_json({"value": "e\u0301"})


def test_non_finite_numbers_are_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json({"value": float("nan")})


def test_digest_binds_every_security_relevant_field() -> None:
    base = {
        "tool_name": "filesystem.write_file",
        "schema_fingerprint": "schema-1",
        "arguments": {"path": "notes.txt", "content": "hello"},
        "run_id": "run-1",
        "policy_digest": "policy-1",
    }
    first = approval_digest(**base)
    for key, replacement in {
        "tool_name": "filesystem.delete_file",
        "schema_fingerprint": "schema-2",
        "arguments": {"path": "other.txt", "content": "hello"},
        "run_id": "run-2",
        "policy_digest": "policy-2",
    }.items():
        changed = json.loads(json.dumps(base))
        changed[key] = replacement
        assert approval_digest(**changed) != first
