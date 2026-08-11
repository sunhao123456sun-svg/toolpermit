from __future__ import annotations

import json
import time
from pathlib import Path

from typer.testing import CliRunner

from toolpermit.approvals import ApprovalService
from toolpermit.audit import AuditStore
from toolpermit.canonical import schema_fingerprint
from toolpermit.cli import app
from toolpermit.domain.models import Decision, DecisionResult, ToolCall


def recorded_call(database: Path) -> str:
    store = AuditStore(database)
    store.initialize()
    store.create_run("run-cli", "observe", ("fixture",), started_at=1.0)
    call = ToolCall(
        event_id="event-cli",
        run_id="run-cli",
        connection_id="connection-cli",
        request_id=1,
        tool_name="echo",
        schema_fingerprint=schema_fingerprint({"type": "object"}),
        arguments={"text": "hello", "token": "sk-never-print-this-secret"},
    )
    decision = DecisionResult(
        decision=Decision.ASK,
        rule_id="$default",
        explanation="Approval required.",
        policy_digest="a" * 64,
    )
    store.record_event(call, decision, occurred_at=2.0)
    approval = ApprovalService(store).create_pending(
        call.event_id,
        call,
        decision.policy_digest,
        expires_at=time.time() + 300,
        approval_id="approval-cli",
    )
    return approval.id


def test_init_refuses_overwrite_and_config_rejects_unknown_keys(tmp_path: Path) -> None:
    runner = CliRunner()
    config = tmp_path / "toolpermit.config.yaml"
    result = runner.invoke(app, ["init", "--config", str(config)])
    assert result.exit_code == 0
    assert config.exists()
    assert (tmp_path / "toolpermit.yaml").exists()

    refused = runner.invoke(app, ["init", "--config", str(config)])
    assert refused.exit_code == 4
    assert "refusing to overwrite" in refused.stderr

    config.write_text("version: 1\nunknown: true\n", encoding="utf-8")
    invalid = runner.invoke(app, ["config", "show", "--config", str(config)])
    assert invalid.exit_code == 3
    assert "Extra inputs are not permitted" in invalid.stderr


def test_cli_approval_runs_export_suggest_and_replay(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    approval_id = recorded_call(database)
    runner = CliRunner()

    pending = runner.invoke(
        app, ["approvals", "list", "--database", str(database), "--json"]
    )
    assert pending.exit_code == 0
    pending_payload = json.loads(pending.stdout)
    assert pending_payload["approvals"][0]["id"] == approval_id
    assert "sk-never-print" not in pending.stdout

    approved = runner.invoke(
        app, ["approvals", "approve", approval_id, "--database", str(database)]
    )
    assert approved.exit_code == 0
    duplicate = runner.invoke(
        app, ["approvals", "approve", approval_id, "--database", str(database)]
    )
    assert duplicate.exit_code == 4

    runs = runner.invoke(app, ["runs", "list", "--database", str(database), "--json"])
    assert runs.exit_code == 0
    assert json.loads(runs.stdout)["runs"][0]["id"] == "run-cli"

    exported = runner.invoke(app, ["audit", "export", "--database", str(database)])
    assert exported.exit_code == 0
    assert json.loads(exported.stdout)["event_id"] == "event-cli"
    assert "sk-never-print" not in exported.stdout

    candidate = tmp_path / "candidate.yaml"
    suggested = runner.invoke(
        app,
        [
            "policy",
            "suggest",
            "--from-run",
            "run-cli",
            "--output",
            str(candidate),
            "--database",
            str(database),
        ],
    )
    assert suggested.exit_code == 0
    assert "inactive until explicitly selected" in candidate.read_text(encoding="utf-8")

    replayed = runner.invoke(
        app,
        ["replay", "--policy", str(candidate), "--database", str(database), "--json"],
    )
    assert replayed.exit_code == 0
    replay_payload = json.loads(replayed.stdout)
    assert replay_payload["schema_version"] == 1
    assert replay_payload["items"][0]["event_id"] == "event-cli"


def test_enforce_wrap_fails_closed_before_spawning_for_missing_policy(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "wrap",
            "--mode",
            "enforce",
            "--policy",
            str(tmp_path / "missing.yaml"),
            "--",
            "python",
            "server.py",
        ],
    )
    assert result.exit_code == 3
    assert "cannot read policy" in result.stderr
