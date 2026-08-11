from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from toolpermit.approvals import ApprovalService
from toolpermit.audit import AuditStore
from toolpermit.canonical import schema_fingerprint
from toolpermit.domain.models import Decision, DecisionResult, ToolCall
from toolpermit.web import create_app

ORIGIN = "http://127.0.0.1:8765"


def pending_approval(database: Path, *, tool_name: str = "filesystem.write") -> str:
    store = AuditStore(database)
    store.initialize()
    store.create_run("run-web", "enforce", ("fixture",), started_at=1.0)
    call = ToolCall(
        event_id="event-web",
        run_id="run-web",
        connection_id="connection-web",
        request_id=1,
        tool_name=tool_name,
        schema_fingerprint=schema_fingerprint({"type": "object"}),
        arguments={"path": "safe.txt", "token": "sk-browser-secret"},
    )
    result = DecisionResult(
        decision=Decision.ASK,
        rule_id="$default",
        explanation="Approval required.",
        policy_digest="b" * 64,
    )
    store.record_event(call, result, occurred_at=2.0)
    approval = ApprovalService(store).create_pending(
        call.event_id,
        call,
        result.policy_digest,
        expires_at=time.time() + 300,
        approval_id="approval-web",
    )
    return approval.id


def client_for(database: Path) -> TestClient:
    return TestClient(create_app(database), base_url=ORIGIN)


def test_ui_refuses_non_loopback_bind(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only supports loopback"):
        create_app(tmp_path / "audit.db", host="0.0.0.0")


def test_security_headers_cookie_host_and_no_cors(tmp_path: Path) -> None:
    client = client_for(tmp_path / "audit.db")
    response = client.get("/")
    assert response.status_code == 200
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "object-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "access-control-allow-origin" not in response.headers
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie

    hostile = client.get("/api/runs", headers={"host": "attacker.example"})
    assert hostile.status_code == 400


def test_origin_and_csrf_protect_shared_approval_service(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    approval_id = pending_approval(database)
    client = client_for(database)
    session = client.get("/api/session")
    token = session.json()["csrf_token"]

    missing = client.post(f"/api/approvals/{approval_id}/approve")
    assert missing.status_code == 403
    hostile = client.post(
        f"/api/approvals/{approval_id}/approve",
        headers={"origin": "https://attacker.example", "x-csrf-token": token},
    )
    assert hostile.status_code == 403
    wrong_token = client.post(
        f"/api/approvals/{approval_id}/approve",
        headers={"origin": ORIGIN, "x-csrf-token": "wrong"},
    )
    assert wrong_token.status_code == 403

    approved = client.post(
        f"/api/approvals/{approval_id}/approve",
        headers={"origin": ORIGIN, "x-csrf-token": token},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "approved"
    duplicate = client.post(
        f"/api/approvals/{approval_id}/approve",
        headers={"origin": ORIGIN, "x-csrf-token": token},
    )
    assert duplicate.status_code == 409


def test_ui_uses_escaped_dom_and_accessible_controls(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    hostile_name = '<img src=x onerror="alert(1)">'
    pending_approval(database, tool_name=hostile_name)
    client = client_for(database)

    html = client.get("/").text
    script = client.get("/app.js").text
    payload = client.get("/api/approvals").json()
    runs = client.get("/api/runs").json()
    matching = client.get(
        "/api/runs/run-web",
        params={
            "decision": "ask",
            "tool": hostile_name,
            "session": "connection-web",
            "rule": "$default",
        },
    ).json()
    not_matching = client.get(
        "/api/runs/run-web", params={"decision": "deny"}
    ).json()
    assert hostile_name not in html
    assert payload["approvals"][0]["event"]["tool_name"] == hostile_name
    assert runs["runs"][0]["id"] == "run-web"
    assert matching["events"][0]["tool_name"] == hostile_name
    assert not_matching["events"] == []
    assert "textContent" in script
    assert "innerHTML" not in script
    assert "eval(" not in script
    assert 'aria-label="Refresh pending approvals and runs"' in html
    assert "setAttribute(\"aria-label\"" in script
    assert ":focus-visible" in client.get("/app.css").text
