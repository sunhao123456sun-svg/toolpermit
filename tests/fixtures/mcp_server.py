from __future__ import annotations

import os
from pathlib import Path

from mcp.server import MCPServer

server = MCPServer("ToolPermit production fixture")


def record(name: str) -> None:
    path = os.environ.get("TOOLPERMIT_FIXTURE_LOG")
    if path:
        with Path(path).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}\n")


@server.tool()
def echo(text: str, token: str = "") -> str:
    """Return text unchanged."""

    record("echo")
    return text


@server.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""

    record("add")
    return a + b


if __name__ == "__main__":
    server.run()

