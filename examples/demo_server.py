"""Contained MCP demo server; writes only below TOOLPERMIT_DEMO_DIR."""

from __future__ import annotations

import os
from pathlib import Path

from mcp.server import MCPServer

server = MCPServer("ToolPermit contained demo")


def _root() -> Path:
    configured = os.environ.get("TOOLPERMIT_DEMO_DIR")
    if not configured:
        raise RuntimeError("TOOLPERMIT_DEMO_DIR is required")
    root = Path(configured).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _contained(relative_path: str) -> Path:
    supplied = Path(relative_path)
    if supplied.is_absolute():
        raise ValueError("demo paths must be relative")
    root = _root()
    target = (root / supplied).resolve()
    if target != root and root not in target.parents:
        raise ValueError("demo path escapes TOOLPERMIT_DEMO_DIR")
    return target


@server.tool()
def write_demo(path: str, content: str, token: str = "demo-not-a-secret") -> str:
    """Write UTF-8 text below the explicitly configured disposable demo directory."""

    del token
    target = _contained(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target.relative_to(_root()))


@server.tool()
def read_demo(path: str) -> str:
    """Read UTF-8 text below the explicitly configured disposable demo directory."""

    return _contained(path).read_text(encoding="utf-8")


if __name__ == "__main__":
    server.run()
