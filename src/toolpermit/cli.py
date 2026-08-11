"""ToolPermit command-line entry point."""

from __future__ import annotations

import typer

from toolpermit import __version__

app = typer.Typer(
    no_args_is_help=True,
    invoke_without_command=True,
    help="Local permission policies for MCP tool calls.",
)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show the ToolPermit version."),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()
