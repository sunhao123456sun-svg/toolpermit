from __future__ import annotations

import concurrent.futures
import json
import sqlite3
from pathlib import Path

from toolpermit.approvals import ApprovalService
from toolpermit.audit import AuditStore
from toolpermit.canonical import approval_digest, schema_fingerprint
from toolpermit.domain.models import ApprovalState, Decision, DecisionResult, ToolCall


def create_event(store: AuditStore, *, secret: str = "safe") -> tuple[ToolCall, DecisionResult]:
    store.create_run("run-1", "enforce", ("python", "server.py"), started_at=1.0)
    call = ToolCall(
        event_id="event-1",
        run_id="run-1",
        connection_id="connection-1",
        request_id=7,
        tool_name="filesystem.write_file",
        schema_fingerprint=schema_fingerprint({"type": "object"}),
        arguments={"path": "fixture.txt", "token": secret},
    )
    result = DecisionResult(
        decision=Decision.ASK,
        rule_id="$default",
        explanation="Approval required.",
        policy_digest="a" * 64,
    )
    store.record_event(call, result, occurred_at=2.0)
    return call, result


def test_migration_and_redaction_before_database_and_export(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    store = AuditStore(database)
    store.initialize()
    secret = "sk-this-secret-must-never-persist"
    create_event(store, secret=secret)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
    assert secret.encode() not in database.read_bytes()
    exported = "\n".join(store.export_jsonl())
    assert secret not in exported
    record = json.loads(exported)
    assert record["redacted_paths"] == ["token"]


def test_approval_is_single_use_and_bound_to_digest(tmp_path: Path) -> None:
    store = AuditStore(tmp_path / "audit.db")
    store.initialize()
    call, decision = create_event(store)
    service = ApprovalService(store)
    approval = service.create_pending(
        call.event_id,
        call,
        decision.policy_digest,
        100.0,
        approval_id="approval-1",
        now=10.0,
    )
    assert service.approve(approval.id, now=11.0)
    assert not service.consume(approval.id, "changed", now=12.0)

    expected = approval_digest(
        tool_name=call.tool_name,
        schema_fingerprint_value=call.schema_fingerprint,
        arguments=call.arguments,
        run_id=call.run_id,
        connection_id=call.connection_id,
        policy_digest_value=decision.policy_digest,
        expires_at=100.0,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = list(
            pool.map(lambda _: service.consume(approval.id, expected, now=12.0), range(32))
        )
    assert results.count(True) == 1
    assert service.get(approval.id).state is ApprovalState.EXECUTING
    assert service.mark_executed(approval.id, now=13.0)
    assert not service.mark_executed(approval.id, now=14.0)


def test_expiry_rejection_cancellation_and_recovery_are_terminal(tmp_path: Path) -> None:
    store = AuditStore(tmp_path / "audit.db")
    store.initialize()
    call, decision = create_event(store)
    service = ApprovalService(store)

    expired = service.create_pending(
        call.event_id, call, decision.policy_digest, 20.0, approval_id="expired", now=10.0
    )
    assert service.expire_due(now=20.0) == 1
    assert service.get(expired.id).state is ApprovalState.EXPIRED
    assert not service.approve(expired.id, now=21.0)

    rejected = service.create_pending(
        call.event_id, call, decision.policy_digest, 40.0, approval_id="rejected", now=30.0
    )
    assert service.reject(rejected.id, now=31.0)
    assert not service.approve(rejected.id, now=32.0)

    cancelled = service.create_pending(
        call.event_id, call, decision.policy_digest, 50.0, approval_id="cancelled", now=40.0
    )
    assert service.cancel(cancelled.id, now=41.0)
    assert service.get(cancelled.id).state is ApprovalState.CANCELLED

    inflight = service.create_pending(
        call.event_id, call, decision.policy_digest, 70.0, approval_id="inflight", now=50.0
    )
    assert service.approve(inflight.id, now=51.0)
    assert service.consume(inflight.id, inflight.request_digest, now=52.0)
    assert service.recover_inflight(now=53.0) == 1
    assert service.get(inflight.id).state is ApprovalState.UNKNOWN
