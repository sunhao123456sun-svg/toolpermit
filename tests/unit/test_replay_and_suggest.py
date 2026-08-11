from __future__ import annotations

from pathlib import Path

from toolpermit.audit import AuditStore
from toolpermit.canonical import schema_fingerprint
from toolpermit.domain.models import Decision, DecisionResult, ToolCall
from toolpermit.policy import parse_policy
from toolpermit.replay import replay_events
from toolpermit.suggest import suggest_policy


def events(tmp_path: Path) -> tuple:
    store = AuditStore(tmp_path / "audit.db")
    store.initialize()
    store.create_run("run-1", "observe", ("fixture",), started_at=1.0)
    result = DecisionResult(
        decision=Decision.ALLOW,
        rule_id="$observe",
        explanation="Observe mode forwards calls.",
        policy_digest="0" * 64,
    )
    for index, arguments in enumerate(
        (
            {"text": "hello", "token": "sk-secret-value-123456"},
            {"text": "world", "token": "sk-secret-value-654321"},
        )
    ):
        call = ToolCall(
            event_id=f"event-{index}",
            run_id="run-1",
            connection_id="connection-1",
            request_id=index,
            tool_name="echo",
            schema_fingerprint=schema_fingerprint({"type": "object"}),
            arguments=arguments,
        )
        store.record_event(call, result, occurred_at=float(index + 2))
    return store.list_events(run_id="run-1")


def test_replay_compares_without_upstream_and_reports_transitions(tmp_path: Path) -> None:
    stored = events(tmp_path)
    baseline = parse_policy("version: 1\ndefault: allow\n")
    candidate = parse_policy("version: 1\ndefault: ask\n")
    report = replay_events(stored, candidate, baseline=baseline)
    assert report.counts() == {"newly_gated": 2}


def test_replay_reports_redacted_match_as_indeterminate(tmp_path: Path) -> None:
    stored = events(tmp_path)
    candidate = parse_policy(
        """
version: 1
default: ask
rules:
  - id: secret-specific
    action: allow
    explanation: Secret-specific historical rule.
    match:
      tool: echo
      arguments:
        token:
          exact: unavailable
"""
    )
    report = replay_events(stored, candidate)
    assert report.counts() == {"indeterminate": 2}


def test_suggestion_is_deterministic_inactive_parseable_and_secret_free(tmp_path: Path) -> None:
    stored = events(tmp_path)
    first = suggest_policy(stored)
    second = suggest_policy(tuple(reversed(stored)))
    assert first == second
    assert "inactive until explicitly selected" in first.content
    assert "sk-secret" not in first.content
    policy = parse_policy(first.content)
    assert policy.default is Decision.ASK
    assert len(policy.rules) == 2

