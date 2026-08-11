"""Real MCP SDK server used by the stdio mediation spike."""

from mcp.server import MCPServer

server = MCPServer("ToolPermit Phase 1 fixture")


@server.tool()
def echo(text: str) -> str:
    """Return text unchanged."""

    return text


@server.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""

    return a + b


if __name__ == "__main__":
    server.run()

