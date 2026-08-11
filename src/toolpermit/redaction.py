"""Irreversible redaction before persistence, logs, export, or display."""

from __future__ import annotations

import re
from typing import Any, cast

REDACTION_VERSION = 1
REDACTED_KEY = "$toolpermit_redacted"
SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|authorization|cookie|credential|password|secret|token)",
    re.IGNORECASE,
)
SECRET_VALUE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|Bearer\s+\S+)",
    re.IGNORECASE,
)


def redacted_sentinel(reason: str) -> dict[str, object]:
    return {REDACTED_KEY: {"version": REDACTION_VERSION, "reason": reason}}


def is_redacted(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    mapping = cast(dict[object, object], value)
    return set(mapping) == {REDACTED_KEY} and isinstance(mapping[REDACTED_KEY], dict)


def redact(value: Any, *, key: str | None = None) -> Any:
    if key is not None and SENSITIVE_KEY.search(key):
        return redacted_sentinel("sensitive-key")
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {
            str(item_key): redact(item, key=str(item_key)) for item_key, item in mapping.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in cast(list[object], value)]
    if isinstance(value, str) and SECRET_VALUE.search(value):
        return redacted_sentinel("credential-pattern")
    return value


def redact_with_report(value: Any) -> tuple[Any, tuple[str, ...]]:
    """Return a redacted copy and sorted paths that were removed."""

    paths: list[str] = []

    def visit(item: object, path: str, key: str | None = None) -> Any:
        if key is not None and SENSITIVE_KEY.search(key):
            paths.append(path)
            return redacted_sentinel("sensitive-key")
        if isinstance(item, dict):
            mapping = cast(dict[object, object], item)
            return {
                str(item_key): visit(
                    child,
                    f"{path}.{item_key}" if path else str(item_key),
                    str(item_key),
                )
                for item_key, child in mapping.items()
            }
        if isinstance(item, list):
            return [
                visit(child, f"{path}.{index}" if path else str(index))
                for index, child in enumerate(cast(list[object], item))
            ]
        if isinstance(item, str) and SECRET_VALUE.search(item):
            paths.append(path)
            return redacted_sentinel("credential-pattern")
        return item

    redacted = visit(value, "")
    return redacted, tuple(sorted(paths))
