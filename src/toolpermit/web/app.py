"""FastAPI application for the local approval and audit interface."""

from __future__ import annotations

import hmac
import secrets
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from toolpermit.application import ToolPermitApplication
from toolpermit.audit import EventRecord

SESSION_COOKIE = "toolpermit_session"
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'; form-action 'self'; connect-src 'self'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
}


def validate_loopback_host(host: str) -> None:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("ToolPermit v0.1 UI only supports loopback hosts")


def _asset(name: str) -> str:
    return files("toolpermit.web.static").joinpath(name).read_text(encoding="utf-8")


def _event_json(event: EventRecord) -> dict[str, object]:
    return {
        "id": event.id,
        "run_id": event.run_id,
        "connection_id": event.connection_id,
        "request_id": event.request_id,
        "occurred_at": event.occurred_at,
        "tool_name": event.tool_name,
        "schema_fingerprint": event.schema_fingerprint,
        "arguments": event.arguments,
        "redacted_paths": list(event.redacted_paths),
        "policy_digest": event.policy_digest,
        "rule_id": event.rule_id,
        "decision": event.decision.value,
        "explanation": event.explanation,
        "lifecycle": event.lifecycle,
        "outcome_metadata": event.outcome_metadata,
        "upstream_duration_ms": event.upstream_duration_ms,
    }


def create_app(
    database: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> FastAPI:
    validate_loopback_host(host)
    application = ToolPermitApplication(database)
    rendered_host = f"[{host}]" if host == "::1" else host
    authority = f"{rendered_host}:{port}"
    origin = f"http://{authority}"
    sessions: dict[str, str] = {}
    app = FastAPI(
        title="ToolPermit local UI",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.middleware("http")
    async def browser_security(  # pyright: ignore[reportUnusedFunction]
        request: Request, call_next: Any
    ) -> Response:
        if request.headers.get("host") != authority:
            response: Response = JSONResponse({"detail": "invalid Host header"}, status_code=400)
        else:
            session_id = request.cookies.get(SESSION_COOKIE)
            new_session = session_id not in sessions
            if new_session:
                session_id = secrets.token_urlsafe(32)
                sessions[session_id] = secrets.token_urlsafe(32)
            request.state.csrf_token = sessions[session_id]
            if request.method in MUTATING_METHODS:
                supplied_origin = request.headers.get("origin")
                supplied_token = request.headers.get("x-csrf-token", "")
                valid_token = hmac.compare_digest(supplied_token, sessions[session_id])
                if supplied_origin != origin or new_session or not valid_token:
                    response = JSONResponse(
                        {"detail": "request origin or CSRF token rejected"}, status_code=403
                    )
                else:
                    response = cast(Response, await call_next(request))
            else:
                response = cast(Response, await call_next(request))
            if new_session:
                response.set_cookie(
                    SESSION_COOKIE,
                    session_id,
                    httponly=True,
                    samesite="strict",
                    secure=False,
                    path="/",
                )
        for name, value in SECURITY_HEADERS.items():
            response.headers[name] = value
        return response

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:  # pyright: ignore[reportUnusedFunction]
        return HTMLResponse(_asset("index.html"))

    @app.get("/app.css")
    async def stylesheet() -> Response:  # pyright: ignore[reportUnusedFunction]
        return Response(_asset("app.css"), media_type="text/css")

    @app.get("/app.js")
    async def javascript() -> Response:  # pyright: ignore[reportUnusedFunction]
        return Response(_asset("app.js"), media_type="text/javascript")

    @app.get("/api/session")
    async def session(  # pyright: ignore[reportUnusedFunction]
        request: Request,
    ) -> dict[str, str]:
        return {"csrf_token": cast(str, request.state.csrf_token)}

    @app.get("/api/approvals")
    async def pending_approvals(  # pyright: ignore[reportUnusedFunction]
    ) -> dict[str, object]:
        records: list[dict[str, object]] = []
        for approval in application.list_pending_approvals():
            event = application.get_event(approval.event_id)
            item = cast(dict[str, object], asdict(approval))
            item["state"] = approval.state.value
            item["event"] = _event_json(event)
            records.append(item)
        return {"schema_version": 1, "approvals": records}

    @app.post("/api/approvals/{approval_id}/approve")
    async def approve(  # pyright: ignore[reportUnusedFunction]
        approval_id: str,
    ) -> dict[str, object]:
        if not application.approve(approval_id, actor="local-ui"):
            raise HTTPException(status_code=409, detail="approval is no longer pending")
        return {"ok": True, "approval_id": approval_id, "state": "approved"}

    @app.post("/api/approvals/{approval_id}/reject")
    async def reject(  # pyright: ignore[reportUnusedFunction]
        approval_id: str,
    ) -> dict[str, object]:
        if not application.reject(approval_id, actor="local-ui"):
            raise HTTPException(status_code=409, detail="approval is no longer pending")
        return {"ok": True, "approval_id": approval_id, "state": "rejected"}

    @app.get("/api/runs")
    async def runs() -> dict[str, object]:  # pyright: ignore[reportUnusedFunction]
        values: list[dict[str, object]] = []
        for run in application.list_runs():
            item = cast(dict[str, object], asdict(run))
            item["upstream_command"] = list(run.upstream_command)
            values.append(item)
        return {"schema_version": 1, "runs": values}

    @app.get("/api/runs/{run_id}")
    async def run_detail(  # pyright: ignore[reportUnusedFunction]
        run_id: str,
        decision: str | None = None,
        tool: str | None = None,
        session: str | None = None,
        rule: str | None = None,
    ) -> dict[str, object]:
        events = application.events_for_run(run_id)
        selected = (
            event
            for event in events
            if (decision is None or event.decision.value == decision)
            and (tool is None or event.tool_name == tool)
            and (session is None or event.connection_id == session)
            and (rule is None or event.rule_id == rule)
        )
        return {"schema_version": 1, "events": [_event_json(event) for event in selected]}

    return app


def run_ui(database: Path, *, host: str = "127.0.0.1", port: int = 8765) -> None:
    validate_loopback_host(host)
    uvicorn.run(create_app(database, host=host, port=port), host=host, port=port, access_log=False)
