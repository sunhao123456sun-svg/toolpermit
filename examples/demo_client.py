"""Drive the contained demo server through ToolPermit."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "examples" / "demo_server.py"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("observe", "enforce"), required=True)
    parser.add_argument("--demo-dir", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=Path(".toolpermit/audit.db"))
    parser.add_argument("--policy", type=Path)
    values = parser.parse_args()
    if values.mode == "enforce" and values.policy is None:
        parser.error("--policy is required in enforce mode")
    return values


async def run(values: argparse.Namespace) -> None:
    demo_dir = values.demo_dir.resolve()
    demo_dir.mkdir(parents=True, exist_ok=True)
    wrapper = [
        "-m",
        "toolpermit.cli",
        "wrap",
        "--mode",
        values.mode,
        "--database",
        str(values.database.resolve()),
    ]
    if values.policy is not None:
        wrapper.extend(("--policy", str(values.policy.resolve())))
    wrapper.extend(("--", sys.executable, str(SERVER)))
    environment = os.environ.copy()
    environment["TOOLPERMIT_DEMO_DIR"] = str(demo_dir)
    parameters = StdioServerParameters(
        command=sys.executable,
        args=wrapper,
        cwd=ROOT,
        env=environment,
    )
    print(f"Contained demo directory: {demo_dir}")
    if values.mode == "enforce":
        print("Waiting for one-time approval before write_demo executes…")
    async with (
        stdio_client(parameters) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        tools = await session.list_tools()
        print("Discovered tools: " + ", ".join(sorted(tool.name for tool in tools.tools)))
        result = await session.call_tool(
            "write_demo",
            arguments={
                "path": "output.txt",
                "content": "ToolPermit contained demo completed.\n",
                "token": "demo-placeholder-not-a-credential",
            },
        )
        if result.is_error:
            raise RuntimeError("demo tool returned an error")
    print(f"Created: {demo_dir / 'output.txt'}")


def main() -> int:
    values = _arguments()
    try:
        asyncio.run(run(values))
    except KeyboardInterrupt:
        print("Demo cancelled; no approval is reused.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
