from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[3]
PROXY = ROOT / "spikes" / "phase1" / "proxy.py"
SERVER = ROOT / "spikes" / "phase1" / "fixture_server.py"
RAW_SERVER = ROOT / "spikes" / "phase1" / "raw_server.py"


def parameters(gate: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[
            str(PROXY),
            "--gate",
            gate,
            "--delay",
            "0.05",
            "--",
            sys.executable,
            str(SERVER),
        ],
        cwd=ROOT,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("gate", ["allow", "delay-allow"])
async def test_real_mcp_sdk_round_trip_through_proxy(gate: str) -> None:
    async with (
        stdio_client(parameters(gate)) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} >= {"echo", "add"}
        result = await session.call_tool("echo", arguments={"text": "through proxy"})
        assert result.content[0].text == "through proxy"  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_modern_2026_discovery_round_trip_through_proxy() -> None:
    async with (
        stdio_client(parameters("allow")) as (read, write),
        ClientSession(read, write) as session,
    ):
        discovered = await session.discover()
        assert "2026-07-28" in discovered.supported_versions
        tools = await session.list_tools()
        assert {tool.name for tool in tools.tools} >= {"echo", "add"}
        result = await session.call_tool("add", arguments={"a": 20, "b": 22})
        assert result.structured_content == {"result": 42}


@pytest.mark.asyncio
async def test_denied_call_does_not_reach_upstream() -> None:
    async with (
        stdio_client(parameters("deny")) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        with pytest.raises(Exception, match="Denied by spike policy"):
            await session.call_tool("add", arguments={"a": 20, "b": 22})


@pytest.mark.asyncio
async def test_cancellation_is_read_while_call_is_waiting(tmp_path: Path) -> None:
    upstream_log = tmp_path / "upstream.log"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(PROXY),
        "--gate",
        "delay-allow",
        "--delay",
        "2",
        "--",
        sys.executable,
        str(RAW_SERVER),
        str(upstream_log),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=ROOT,
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
    await asyncio.sleep(0.05)
    process.stdin.write((json.dumps(cancellation) + "\n").encode())
    await process.stdin.drain()

    response = json.loads(await asyncio.wait_for(process.stdout.readline(), timeout=1))
    assert response["id"] == 91
    assert response["error"]["code"] == -32800

    process.stdin.close()
    await process.stdin.wait_closed()
    assert await asyncio.wait_for(process.wait(), timeout=5) == 0
    assert not upstream_log.exists() or "tools/call" not in upstream_log.read_text()
