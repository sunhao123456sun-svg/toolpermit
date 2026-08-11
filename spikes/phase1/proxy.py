"""Wire-level MCP stdio mediation spike.

This intentionally stays outside the production package. It validates that a
bidirectional line proxy can gate tool calls while continuing to read client
cancellation messages.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

TOOL_CALL_METHODS = {"tools/call"}
CANCEL_METHODS = {"notifications/cancelled", "requests/cancel"}


def _request_id(message: dict[str, Any]) -> str | int | None:
    value = message.get("id")
    return value if isinstance(value, (str, int)) else None


def _cancelled_id(message: dict[str, Any]) -> str | int | None:
    params = message.get("params")
    if not isinstance(params, dict):
        return None
    value = params.get("requestId", params.get("id"))
    return value if isinstance(value, (str, int)) else None


def _error(request_id: str | int, code: int, text: str) -> bytes:
    value = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": text},
    }
    return (json.dumps(value, separators=(",", ":")) + "\n").encode()


@dataclass
class Proxy:
    process: asyncio.subprocess.Process
    gate: str
    delay: float
    upstream_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    client_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending: dict[str | int, asyncio.Task[None]] = field(default_factory=dict)

    async def write_upstream(self, line: bytes) -> None:
        if self.process.stdin is None:
            raise RuntimeError("upstream stdin is unavailable")
        async with self.upstream_lock:
            self.process.stdin.write(line)
            await self.process.stdin.drain()

    async def write_client(self, line: bytes) -> None:
        async with self.client_lock:
            await asyncio.to_thread(self._write_client_sync, line)

    @staticmethod
    def _write_client_sync(line: bytes) -> None:
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()

    async def gated_call(self, request_id: str | int, line: bytes) -> None:
        try:
            if self.gate == "deny":
                await self.write_client(_error(request_id, -32001, "Denied by spike policy"))
                return
            if self.gate == "delay-allow":
                await asyncio.sleep(self.delay)
            await self.write_upstream(line)
        except asyncio.CancelledError:
            await self.write_client(_error(request_id, -32800, "Cancelled before execution"))
            raise
        finally:
            self.pending.pop(request_id, None)

    async def client_to_upstream(self) -> None:
        while True:
            line = await asyncio.to_thread(sys.stdin.buffer.readline)
            if not line:
                break
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                await self.write_upstream(line)
                continue
            if not isinstance(message, dict):
                await self.write_upstream(line)
                continue

            method = message.get("method")
            if method in CANCEL_METHODS:
                cancelled_id = _cancelled_id(message)
                pending = self.pending.get(cancelled_id) if cancelled_id is not None else None
                if pending is not None and not pending.done():
                    pending.cancel()
                    continue
                await self.write_upstream(line)
                continue

            request_id = _request_id(message)
            if method in TOOL_CALL_METHODS and request_id is not None:
                task = asyncio.create_task(self.gated_call(request_id, line))
                self.pending[request_id] = task
                continue
            await self.write_upstream(line)

        if self.pending:
            await asyncio.gather(*self.pending.values(), return_exceptions=True)
        if self.process.stdin is not None:
            self.process.stdin.close()
            await self.process.stdin.wait_closed()

    async def upstream_to_client(self) -> None:
        if self.process.stdout is None:
            raise RuntimeError("upstream stdout is unavailable")
        while line := await self.process.stdout.readline():
            await self.write_client(line)


async def run(args: argparse.Namespace) -> int:
    environment = os.environ.copy()
    process = await asyncio.create_subprocess_exec(
        *args.command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=sys.stderr,
        env=environment,
    )
    proxy = Proxy(process=process, gate=args.gate, delay=args.delay)
    try:
        await asyncio.gather(proxy.client_to_upstream(), proxy.upstream_to_client())
    finally:
        if process.returncode is None:
            process.terminate()
        await process.wait()
    return int(process.returncode or 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", choices=("allow", "deny", "delay-allow"), default="allow")
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    if arguments.command and arguments.command[0] == "--":
        arguments.command = arguments.command[1:]
    if not arguments.command:
        parser.error("an upstream command is required after --")
    return arguments


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))

