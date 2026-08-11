"""Bidirectional MCP stdio proxy with policy, approval, and audit mediation."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from toolpermit.approvals import ApprovalService
from toolpermit.audit import AuditStore
from toolpermit.canonical import schema_fingerprint
from toolpermit.domain.models import ApprovalState, Decision, DecisionResult, ToolCall
from toolpermit.policy import Policy, load_policy

TOOL_CALL_METHOD = "tools/call"
TOOL_LIST_METHOD = "tools/list"
CANCEL_METHODS = {"notifications/cancelled", "requests/cancel"}


class DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"invalid JSON numeric constant: {value}")


def _parse_message(line: bytes) -> dict[str, object]:
    value = cast(
        object,
        json.loads(
            line,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        ),
    )
    if not isinstance(value, dict):
        raise ValueError("JSON-RPC message must be an object")
    return cast(dict[str, object], value)


def _request_id(message: dict[str, object]) -> str | int | None:
    value = message.get("id")
    if isinstance(value, bool):
        return None
    return value if isinstance(value, (str, int)) else None


def _cancelled_id(message: dict[str, object]) -> str | int | None:
    params = message.get("params")
    if not isinstance(params, dict):
        return None
    mapping = cast(dict[str, object], params)
    value = mapping.get("requestId", mapping.get("id"))
    if isinstance(value, bool):
        return None
    return value if isinstance(value, (str, int)) else None


def _response(request_id: str | int | None, code: int, text: str) -> bytes:
    value = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": text},
    }
    return (json.dumps(value, separators=(",", ":")) + "\n").encode()


def _content_types(message: dict[str, object]) -> tuple[bool, tuple[str, ...]]:
    if "error" in message:
        return True, ()
    result = message.get("result")
    if not isinstance(result, dict):
        return False, ()
    result_mapping = cast(dict[str, object], result)
    is_error = result_mapping.get("isError") is True
    content = result_mapping.get("content")
    if not isinstance(content, list):
        return is_error, ()
    types: list[str] = []
    for item in cast(list[object], content):
        if isinstance(item, dict):
            item_type = cast(dict[str, object], item).get("type")
            if isinstance(item_type, str):
                types.append(item_type)
    return is_error, tuple(sorted(set(types)))


@dataclass(frozen=True)
class ProxyConfig:
    mode: str
    database: Path
    command: tuple[str, ...]
    policy: Policy | None = None
    approval_ttl: float = 300.0
    poll_interval: float = 0.1
    max_line_bytes: int = 4 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.mode not in {"observe", "enforce"}:
            raise ValueError("mode must be observe or enforce")
        if self.mode == "enforce" and self.policy is None:
            raise ValueError("enforce mode requires a valid policy")
        if not self.command:
            raise ValueError("an upstream command is required")
        if self.approval_ttl <= 0 or self.poll_interval <= 0:
            raise ValueError("approval timing values must be positive")


@dataclass(frozen=True)
class _Execution:
    event_id: str
    started_at: float
    approval_id: str | None


def _task_map() -> dict[str | int, asyncio.Task[None]]:
    return {}


def _approval_id_map() -> dict[str | int, str]:
    return {}


def _execution_map() -> dict[str | int, _Execution]:
    return {}


def _request_set() -> set[str | int]:
    return set()


def _catalog_map() -> dict[str, str]:
    return {}


@dataclass
class MCPProxy:
    config: ProxyConfig
    process: asyncio.subprocess.Process
    store: AuditStore
    approvals: ApprovalService
    run_id: str
    connection_id: str
    upstream_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    client_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending: dict[str | int, asyncio.Task[None]] = field(default_factory=_task_map)
    pending_approval_ids: dict[str | int, str] = field(default_factory=_approval_id_map)
    executions: dict[str | int, _Execution] = field(default_factory=_execution_map)
    list_requests: set[str | int] = field(default_factory=_request_set)
    cancelled_requests: set[str | int] = field(default_factory=_request_set)
    catalog: dict[str, str] = field(default_factory=_catalog_map)

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

    async def client_to_upstream(self) -> None:
        while True:
            line = await asyncio.to_thread(
                sys.stdin.buffer.readline, self.config.max_line_bytes + 1
            )
            if not line:
                break
            if len(line) > self.config.max_line_bytes:
                await self.write_client(_response(None, -32600, "Message exceeds size limit"))
                continue
            try:
                message = _parse_message(line)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                await self.write_client(_response(None, -32700, "Invalid JSON-RPC message"))
                continue
            method = message.get("method")
            if method in CANCEL_METHODS:
                await self._handle_cancellation(message, line)
                continue
            request_id = _request_id(message)
            if method == TOOL_LIST_METHOD and request_id is not None:
                self.list_requests.add(request_id)
            if method == TOOL_CALL_METHOD and request_id is not None:
                task = asyncio.create_task(self._handle_tool_call(request_id, message, line))
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
        while True:
            try:
                line = await self.process.stdout.readline()
            except ValueError:
                await self.write_client(
                    _response(None, -32603, "Upstream message exceeds size limit")
                )
                break
            if not line:
                break
            try:
                message = _parse_message(line)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                await self.write_client(
                    _response(None, -32603, "Invalid upstream JSON-RPC message")
                )
                continue
            request_id = _request_id(message)
            if request_id is not None and request_id in self.list_requests:
                self.list_requests.discard(request_id)
                self._update_catalog(message)
            execution = self.executions.pop(request_id, None) if request_id is not None else None
            if execution is not None:
                is_error, types = _content_types(message)
                duration_ms = (time.monotonic() - execution.started_at) * 1000
                lifecycle = "failed" if is_error else "executed"
                await asyncio.to_thread(
                    self.store.record_outcome,
                    execution.event_id,
                    is_error=is_error,
                    content_types=types,
                    duration_ms=duration_ms,
                    lifecycle=lifecycle,
                )
                if execution.approval_id is not None:
                    if is_error:
                        await asyncio.to_thread(
                            self.approvals.mark_failed,
                            execution.approval_id,
                            "upstream returned an error",
                        )
                    else:
                        await asyncio.to_thread(
                            self.approvals.mark_executed, execution.approval_id
                        )
            await self.write_client(line)

    async def _handle_tool_call(
        self,
        request_id: str | int,
        message: dict[str, object],
        line: bytes,
    ) -> None:
        try:
            call = self._make_call(request_id, message)
        except ValueError as error:
            await self.write_client(_response(request_id, -32602, str(error)))
            self.pending.pop(request_id, None)
            return

        if self.config.mode == "observe":
            result = DecisionResult(
                decision=Decision.ALLOW,
                rule_id="$observe",
                explanation="Observe mode does not enforce policy; call forwarded.",
                policy_digest="0" * 64,
            )
        else:
            if self.config.policy is None:
                result = DecisionResult(
                    decision=Decision.DENY,
                    rule_id="$error",
                    explanation="Enforcement policy is unavailable.",
                    policy_digest="0" * 64,
                )
            else:
                try:
                    from toolpermit.policy import evaluate

                    result = evaluate(call, self.config.policy)
                except Exception:
                    result = DecisionResult(
                        decision=Decision.DENY,
                        rule_id="$evaluation-error",
                        explanation="Policy evaluation failed closed.",
                        policy_digest="0" * 64,
                    )
        lifecycle = "observed" if self.config.mode == "observe" else "decided"
        await asyncio.to_thread(self.store.record_event, call, result, lifecycle=lifecycle)

        if request_id in self.cancelled_requests:
            await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "cancelled")
            self._finish_pending(request_id)
            return

        if result.decision is Decision.DENY:
            await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "denied")
            await self.write_client(
                _response(request_id, -32001, f"Denied by ToolPermit rule {result.rule_id}")
            )
            self.pending.pop(request_id, None)
            return
        if result.decision is Decision.ALLOW:
            await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "executing")
            if request_id in self.cancelled_requests:
                await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "cancelled")
                self._finish_pending(request_id)
                return
            self._finish_pending(request_id)
            self.executions[request_id] = _Execution(call.event_id, time.monotonic(), None)
            await self.write_upstream(line)
            return

        expires_at = time.time() + self.config.approval_ttl
        approval = await asyncio.to_thread(
            self.approvals.create_pending,
            call.event_id,
            call,
            result.policy_digest,
            expires_at,
        )
        self.pending_approval_ids[request_id] = approval.id
        await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "pending")
        if request_id in self.cancelled_requests:
            await asyncio.to_thread(self.approvals.cancel, approval.id)
            await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "cancelled")
            self._finish_pending(request_id)
            return
        await self._wait_for_approval(request_id, call, line, approval.id, approval.request_digest)

    async def _wait_for_approval(
        self,
        request_id: str | int,
        call: ToolCall,
        line: bytes,
        approval_id: str,
        request_digest: str,
    ) -> None:
        try:
            while True:
                if request_id in self.cancelled_requests:
                    await asyncio.to_thread(self.approvals.cancel, approval_id)
                    await asyncio.to_thread(
                        self.store.update_lifecycle, call.event_id, "cancelled"
                    )
                    return
                record = await asyncio.to_thread(self.approvals.get, approval_id)
                if record.state is ApprovalState.APPROVED:
                    consumed = await asyncio.to_thread(
                        self.approvals.consume, approval_id, request_digest
                    )
                    if consumed:
                        self.pending.pop(request_id, None)
                        self.pending_approval_ids.pop(request_id, None)
                        self.executions[request_id] = _Execution(
                            call.event_id, time.monotonic(), approval_id
                        )
                        await asyncio.to_thread(
                            self.store.update_lifecycle, call.event_id, "executing"
                        )
                        await self.write_upstream(line)
                        return
                elif record.state in {
                    ApprovalState.REJECTED,
                    ApprovalState.EXPIRED,
                    ApprovalState.CANCELLED,
                    ApprovalState.UNKNOWN,
                }:
                    await asyncio.to_thread(
                        self.store.update_lifecycle, call.event_id, record.state.value
                    )
                    await self.write_client(
                        _response(
                            request_id,
                            -32002,
                            f"ToolPermit approval ended as {record.state.value}",
                        )
                    )
                    return
                await asyncio.sleep(self.config.poll_interval)
        except asyncio.CancelledError:
            await asyncio.to_thread(self.approvals.cancel, approval_id)
            await asyncio.to_thread(self.store.update_lifecycle, call.event_id, "cancelled")
            raise
        finally:
            self._finish_pending(request_id)

    async def _handle_cancellation(self, message: dict[str, object], line: bytes) -> None:
        request_id = _cancelled_id(message)
        task = self.pending.get(request_id) if request_id is not None else None
        if request_id is not None and task is not None and not task.done():
            approval_id = self.pending_approval_ids.get(request_id)
            if approval_id is not None and not await asyncio.to_thread(
                self.approvals.cancel, approval_id
            ):
                await self.write_upstream(line)
                return
            self.cancelled_requests.add(request_id)
            await self.write_client(_response(request_id, -32800, "Cancelled before execution"))
            return
        await self.write_upstream(line)

    def _finish_pending(self, request_id: str | int) -> None:
        self.pending.pop(request_id, None)
        self.pending_approval_ids.pop(request_id, None)
        self.cancelled_requests.discard(request_id)

    def _make_call(self, request_id: str | int, message: dict[str, object]) -> ToolCall:
        params = message.get("params")
        if not isinstance(params, dict):
            raise ValueError("tools/call params must be an object")
        mapping = cast(dict[str, object], params)
        name = mapping.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("tools/call requires a non-empty tool name")
        arguments = mapping.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError("tools/call arguments must be an object")
        return ToolCall(
            event_id=f"evt_{uuid.uuid4().hex}",
            run_id=self.run_id,
            connection_id=self.connection_id,
            request_id=request_id,
            tool_name=name,
            schema_fingerprint=self.catalog.get(name, schema_fingerprint({})),
            arguments=cast(dict[str, Any], arguments),
        )

    def _update_catalog(self, message: dict[str, object]) -> None:
        result = message.get("result")
        if not isinstance(result, dict):
            return
        tools = cast(dict[str, object], result).get("tools")
        if not isinstance(tools, list):
            return
        for item in cast(list[object], tools):
            if not isinstance(item, dict):
                continue
            tool = cast(dict[str, object], item)
            name = tool.get("name")
            input_schema = tool.get("inputSchema", {})
            if isinstance(name, str) and isinstance(input_schema, dict):
                self.catalog[name] = schema_fingerprint(cast(dict[str, Any], input_schema))


async def run_proxy(config: ProxyConfig) -> int:
    store = AuditStore(config.database)
    store.initialize()
    approvals = ApprovalService(store)
    await asyncio.to_thread(approvals.recover_inflight)
    run_id = f"run_{uuid.uuid4().hex}"
    connection_id = f"conn_{uuid.uuid4().hex}"
    store.create_run(run_id, config.mode, config.command)
    process = await asyncio.create_subprocess_exec(
        *config.command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=sys.stderr,
        env=os.environ.copy(),
        limit=config.max_line_bytes + 1,
    )
    proxy = MCPProxy(config, process, store, approvals, run_id, connection_id)
    try:
        await asyncio.gather(proxy.client_to_upstream(), proxy.upstream_to_client())
    finally:
        for task in tuple(proxy.pending.values()):
            task.cancel()
        if process.returncode is None:
            try:
                await asyncio.wait_for(process.wait(), timeout=1.0)
            except TimeoutError:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except TimeoutError:
                    process.kill()
                    await process.wait()
        else:
            await process.wait()
        store.finish_run(run_id)
    return int(process.returncode or 0)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="toolpermit-mcp-proxy")
    parser.add_argument("--mode", choices=("observe", "enforce"), required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--approval-ttl", type=float, default=300.0)
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    if arguments.command and arguments.command[0] == "--":
        arguments.command = arguments.command[1:]
    if not arguments.command:
        parser.error("an upstream command is required after --")
    if arguments.mode == "enforce" and arguments.policy is None:
        parser.error("--policy is required in enforce mode")
    return arguments


def main() -> int:
    arguments = _arguments()
    policy = load_policy(arguments.policy) if arguments.policy is not None else None
    if arguments.mode == "observe":
        print("WARNING: observe mode records calls but does not enforce policy", file=sys.stderr)
    config = ProxyConfig(
        mode=arguments.mode,
        database=arguments.database,
        command=tuple(arguments.command),
        policy=policy,
        approval_ttl=arguments.approval_ttl,
        poll_interval=arguments.poll_interval,
    )
    return asyncio.run(run_proxy(config))


if __name__ == "__main__":
    raise SystemExit(main())
