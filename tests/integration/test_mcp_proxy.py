from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from toolpermit.approvals import ApprovalService
from toolpermit.audit import AuditStore
from toolpermit.domain.models import ApprovalState, Decision

ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "tests" / "fixtures" / "mcp_server.py"
RAW_SERVER = ROOT / "tests" / "fixtures" / "raw_server.py"


def write_policy(path: Path, default: str) -> Path:
    path.write_text(f"version: 1\ndefault: {default}\n", encoding="utf-8")
    return path


def parameters(database: Path, mode: str, policy: Path | None = None) -> StdioServerParameters:
    args = [
        "-m",
        "toolpermit.protocol.mcp.proxy",
        "--mode",
        mode,
        "--database",
        str(database),
    ]
    if policy is not None:
        args.extend(("--policy", str(policy)))
    args.extend(("--", sys.executable, str(SERVER)))
    return StdioServerParameters(
        command=sys.executable,
        args=args,
        cwd=ROOT,
        env=os.environ.copy(),
    )


@pytest.mark.asyncio
async def test_observe_round_trip_records_redacted_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "audit.db"
    log = tmp_path / "upstream.log"
    monkeypatch.setenv("TOOLPERMIT_FIXTURE_LOG", str(log))
    async with (
        stdio_client(parameters(database, "observe")) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} >= {"echo", "add"}
        result = await session.call_tool(
            "echo", arguments={"text": "observed", "token": "sk-secret-1234567890"}
        )
        assert result.content[0].text == "observed"  # type: ignore[attr-defined]

    store = AuditStore(database)
    events = store.list_events()
    assert len(events) == 1
    assert events[0].decision is Decision.ALLOW
    assert events[0].redacted_paths == ("token",)
    assert "sk-secret" not in database.read_text(encoding="utf-8", errors="ignore")
    assert log.read_text() == "echo\n"


@pytest.mark.asyncio
async def test_modern_discovery_round_trip(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    async with (
        stdio_client(parameters(database, "observe")) as (read, write),
        ClientSession(read, write) as session,
    ):
        discovered = await session.discover()
        assert "2026-07-28" in discovered.supported_versions
        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} >= {"echo", "add"}


@pytest.mark.asyncio
async def test_deny_never_reaches_upstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "audit.db"
    log = tmp_path / "upstream.log"
    monkeypatch.setenv("TOOLPERMIT_FIXTURE_LOG", str(log))
    policy = write_policy(tmp_path / "deny.yaml", "deny")
    async with (
        stdio_client(parameters(database, "enforce", policy)) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await session.list_tools()
        with pytest.raises(Exception, match="Denied by ToolPermit"):
            await session.call_tool("add", arguments={"a": 20, "b": 22})
    assert not log.exists()
    event = AuditStore(database).list_events()[0]
    assert event.lifecycle == "denied"


@pytest.mark.asyncio
async def test_ask_resumes_only_after_external_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "audit.db"
    log = tmp_path / "upstream.log"
    monkeypatch.setenv("TOOLPERMIT_FIXTURE_LOG", str(log))
    policy = write_policy(tmp_path / "ask.yaml", "ask")
    async with (
        stdio_client(parameters(database, "enforce", policy)) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        await session.list_tools()
        task = asyncio.create_task(session.call_tool("add", arguments={"a": 20, "b": 22}))
        service = ApprovalService(AuditStore(database))
        deadline = time.monotonic() + 5
        pending = ()
        while time.monotonic() < deadline and not pending:
            pending = await asyncio.to_thread(service.list_pending)
            await asyncio.sleep(0.05)
        assert len(pending) == 1
        assert not log.exists()
        assert await asyncio.to_thread(service.approve, pending[0].id)
        result = await asyncio.wait_for(task, timeout=5)
        assert result.structured_content == {"result": 42}
        assert service.get(pending[0].id).state is ApprovalState.EXECUTED
    assert log.read_text() == "add\n"


@pytest.mark.asyncio
async def test_cancellation_while_waiting_never_forwards(tmp_path: Path) -> None:
    database = tmp_path / "audit.db"
    policy = write_policy(tmp_path / "ask.yaml", "ask")
    upstream_log = tmp_path / "raw-upstream.log"
    command = [
        sys.executable,
        "-m",
        "toolpermit.protocol.mcp.proxy",
        "--mode",
        "enforce",
        "--database",
        str(database),
        "--policy",
        str(policy),
        "--poll-interval",
        "0.02",
        "--",
        sys.executable,
        str(RAW_SERVER),
        str(upstream_log),
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=ROOT,
        env=os.environ.copy(),
    )
    assert process.stdin is not None
    assert process.stdout is not None
    request = {
        "jsonrpc": "2.0",
        "id": 91,
        "method": "tools/call",
        "params": {"name": "dangerous", "arguments": {}},
    }
    cancellation = {
        "jsonrpc": "2.0",
        "method": "notifications/cancelled",
        "params": {"requestId": 91, "reason": "test cancellation"},
    }
    process.stdin.write((json.dumps(request) + "\n").encode())
    await process.stdin.drain()
    service = ApprovalService(AuditStore(database))
    deadline = time.monotonic() + 5
    pending = ()
    while time.monotonic() < deadline and not pending:
        with contextlib.suppress(sqlite3.OperationalError):
            pending = await asyncio.to_thread(service.list_pending)
        await asyncio.sleep(0.05)
    assert len(pending) == 1
    process.stdin.write((json.dumps(cancellation) + "\n").encode())
    await process.stdin.drain()
    response = json.loads(await asyncio.wait_for(process.stdout.readline(), timeout=5))
    assert response["error"]["code"] == -32800
    process.stdin.close()
    await process.stdin.wait_closed()
    assert await asyncio.wait_for(process.wait(), timeout=5) == 0
    assert not upstream_log.exists()
    assert service.get(pending[0].id).state is ApprovalState.CANCELLED
