"""Evaluate stored redacted events without starting an upstream process."""

from __future__ import annotations

from dataclasses import dataclass

from toolpermit.audit.store import EventRecord
from toolpermit.domain.models import Decision, ToolCall
from toolpermit.policy import Policy, evaluate


@dataclass(frozen=True)
class ReplayItem:
    event_id: str
    baseline: Decision | None
    candidate: Decision
    transition: str
    baseline_rule_id: str | None
    candidate_rule_id: str
    indeterminate: bool
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class ReplayReport:
    schema_version: int
    items: tuple[ReplayItem, ...]

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in self.items:
            result[item.transition] = result.get(item.transition, 0) + 1
        return dict(sorted(result.items()))


def _transition(baseline: Decision | None, candidate: Decision) -> str:
    if baseline is None:
        return "evaluated"
    if baseline is candidate:
        return "unchanged"
    if candidate is Decision.ALLOW:
        return "newly_allowed"
    if candidate is Decision.ASK:
        return "newly_gated"
    return "newly_denied"


def replay_events(
    events: tuple[EventRecord, ...],
    candidate: Policy,
    *,
    baseline: Policy | None = None,
) -> ReplayReport:
    items: list[ReplayItem] = []
    for event in events:
        call = ToolCall(
            event_id=event.id,
            run_id=event.run_id,
            connection_id=event.connection_id,
            request_id=event.request_id,
            tool_name=event.tool_name,
            schema_fingerprint=event.schema_fingerprint,
            arguments=event.arguments,
        )
        candidate_result = evaluate(call, candidate, replay=True)
        baseline_result = evaluate(call, baseline, replay=True) if baseline is not None else None
        indeterminate = candidate_result.indeterminate or bool(
            baseline_result is not None and baseline_result.indeterminate
        )
        transition = (
            "indeterminate"
            if indeterminate
            else _transition(
                baseline_result.decision if baseline_result is not None else None,
                candidate_result.decision,
            )
        )
        diagnostics = candidate_result.diagnostics
        if baseline_result is not None:
            diagnostics += baseline_result.diagnostics
        items.append(
            ReplayItem(
                event_id=event.id,
                baseline=baseline_result.decision if baseline_result is not None else None,
                candidate=candidate_result.decision,
                transition=transition,
                baseline_rule_id=baseline_result.rule_id if baseline_result is not None else None,
                candidate_rule_id=candidate_result.rule_id,
                indeterminate=indeterminate,
                diagnostics=diagnostics,
            )
        )
    return ReplayReport(schema_version=1, items=tuple(items))

