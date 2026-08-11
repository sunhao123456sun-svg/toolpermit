from __future__ import annotations

import pytest

from toolpermit.canonical import schema_fingerprint
from toolpermit.domain.models import Decision, ToolCall
from toolpermit.policy import PolicyLoadError, evaluate, lint_policy, parse_policy
from toolpermit.redaction import redact


def call(tool: str, arguments: dict[str, object]) -> ToolCall:
    return ToolCall(
        event_id="event-1",
        run_id="run-1",
        connection_id="connection-1",
        request_id=1,
        tool_name=tool,
        schema_fingerprint=schema_fingerprint({"type": "object"}),
        arguments=arguments,
    )


POLICY = """
version: 1
default: ask
rules:
  - id: deny-delete
    action: deny
    explanation: Deletion requires a different workflow.
    match:
      tool: filesystem.delete_file
  - id: allow-safe-write
    action: allow
    explanation: Writes to the disposable fixture are allowed.
    match:
      tool: filesystem.write_file
      arguments:
        path:
          path_under: fixtures/disposable
        content:
          glob: "public-*"
"""


def test_first_match_and_explicit_default() -> None:
    policy = parse_policy(POLICY)
    denied = evaluate(call("filesystem.delete_file", {"path": "fixtures/disposable/a"}), policy)
    allowed = evaluate(
        call("filesystem.write_file", {"path": "fixtures/disposable/a", "content": "public-a"}),
        policy,
    )
    asked = evaluate(call("network.fetch", {"url": "https://example.com"}), policy)
    assert (denied.decision, denied.rule_id) == (Decision.DENY, "deny-delete")
    assert (allowed.decision, allowed.rule_id) == (Decision.ALLOW, "allow-safe-write")
    assert (asked.decision, asked.rule_id) == (Decision.ASK, "$default")


def test_path_under_is_lexical_and_rejects_parent_traversal() -> None:
    policy = parse_policy(POLICY)
    result = evaluate(
        call(
            "filesystem.write_file",
            {"path": "fixtures/disposable/../outside", "content": "public-a"},
        ),
        policy,
    )
    assert result.decision is Decision.ASK


def test_redacted_required_value_is_indeterminate_during_replay() -> None:
    policy = parse_policy(
        """
version: 1
default: ask
rules:
  - id: exact-token
    action: allow
    explanation: Exact fixture token.
    match:
      tool: auth.test
      arguments:
        token:
          exact: expected
"""
    )
    result = evaluate(call("auth.test", redact({"token": "expected"})), policy, replay=True)
    assert result.decision is Decision.DENY
    assert result.indeterminate


@pytest.mark.parametrize(
    "text",
    [
        "version: 1\ndefault: allow\nunknown: true\n",
        "version: 2\ndefault: ask\n",
        """version: 1
default: ask
rules:
- id: same
  action: deny
  explanation: first
  match: {}
- id: same
  action: allow
  explanation: second
  match: {}
""",
        "!!python/object/apply:os.system ['echo unsafe']",
    ],
)
def test_invalid_policy_fails_closed(text: str) -> None:
    with pytest.raises(PolicyLoadError):
        parse_policy(text)


def test_linter_reports_shadowing_and_broad_allow() -> None:
    policy = parse_policy(
        """
version: 1
default: deny
rules:
  - id: everything
    action: allow
    explanation: Too broad.
    match: {}
  - id: unreachable
    action: deny
    explanation: Never reached.
    match:
      tool: dangerous
"""
    )
    warnings = lint_policy(policy)
    assert len(warnings) == 2
