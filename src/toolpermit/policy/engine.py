"""Pure, ordered, first-match policy evaluation."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Any, cast

from toolpermit.canonical import policy_digest
from toolpermit.domain.models import Decision, DecisionResult, ToolCall
from toolpermit.policy.models import (
    Condition,
    ExactCondition,
    GlobCondition,
    Policy,
)
from toolpermit.redaction import is_redacted


@dataclass(frozen=True)
class _MatchResult:
    matched: bool
    indeterminate: bool = False
    diagnostic: str | None = None


def _lookup_path(arguments: dict[str, Any], path: str) -> tuple[bool, object]:
    current: object = arguments
    for part in path.split("."):
        if isinstance(current, dict):
            mapping = cast(dict[str, object], current)
            if part not in mapping:
                return False, None
            current = mapping[part]
        elif isinstance(current, list):
            sequence = cast(list[object], current)
            if not part.isdecimal() or int(part) >= len(sequence):
                return False, None
            current = sequence[int(part)]
        else:
            return False, None
    return True, current


def _lexical_parts(path: str) -> tuple[str, ...] | None:
    normalized = path.replace("\\", "/")
    parts = tuple(part for part in normalized.split("/") if part not in ("", "."))
    if ".." in parts:
        return None
    return parts


def _path_is_under(value: str, root: str) -> bool:
    candidate = _lexical_parts(value)
    parent = _lexical_parts(root)
    if candidate is None or parent is None or not parent:
        return False
    return candidate[: len(parent)] == parent


def _condition_matches(value: object, condition: Condition, path: str) -> _MatchResult:
    if is_redacted(value):
        return _MatchResult(False, True, f"argument {path!r} is redacted")
    if isinstance(condition, ExactCondition):
        return _MatchResult(value == condition.exact)
    if isinstance(condition, GlobCondition):
        return _MatchResult(isinstance(value, str) and fnmatch.fnmatchcase(value, condition.glob))
    return _MatchResult(isinstance(value, str) and _path_is_under(value, condition.path_under))


def _rule_matches(
    call: ToolCall,
    tool: str | None,
    conditions: dict[str, Condition],
) -> _MatchResult:
    if tool is not None and call.tool_name != tool:
        return _MatchResult(False)
    diagnostics: list[str] = []
    for path, condition in conditions.items():
        found, value = _lookup_path(call.arguments, path)
        if not found:
            return _MatchResult(False)
        result = _condition_matches(value, condition, path)
        if result.indeterminate:
            diagnostics.append(result.diagnostic or f"argument {path!r} is unavailable")
            continue
        if not result.matched:
            return _MatchResult(False)
    if diagnostics:
        return _MatchResult(False, True, "; ".join(diagnostics))
    return _MatchResult(True)


def evaluate(call: ToolCall, policy: Policy, *, replay: bool = False) -> DecisionResult:
    digest = policy_digest(policy.model_dump(mode="json"))
    for rule in policy.rules:
        match = _rule_matches(call, rule.match.tool, rule.match.arguments.root)
        if match.indeterminate:
            if replay:
                return DecisionResult(
                    decision=Decision.DENY,
                    rule_id=rule.id,
                    explanation="Replay is indeterminate because a required value was redacted.",
                    policy_digest=digest,
                    indeterminate=True,
                    diagnostics=(match.diagnostic or "redacted argument",),
                )
            continue
        if match.matched:
            return DecisionResult(
                decision=rule.action,
                rule_id=rule.id,
                explanation=rule.explanation,
                policy_digest=digest,
            )
    return DecisionResult(
        decision=policy.default,
        rule_id="$default",
        explanation=f"No rule matched; explicit default is {policy.default.value}.",
        policy_digest=digest,
    )


def lint_policy(policy: Policy) -> tuple[str, ...]:
    warnings: list[str] = []
    for index, rule in enumerate(policy.rules):
        is_global = rule.match.tool is None and not rule.match.arguments.root
        if is_global and index < len(policy.rules) - 1:
            warnings.append(f"rule {rule.id!r} matches every call and shadows later rules")
        if rule.action is Decision.ALLOW and not rule.match.arguments.root:
            warnings.append(f"rule {rule.id!r} broadly allows a tool without argument constraints")
    return tuple(warnings)
