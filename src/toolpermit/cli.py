"""ToolPermit command-line interface."""

from __future__ import annotations

import asyncio
import json
from enum import IntEnum
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from toolpermit import __version__
from toolpermit.application import ToolPermitApplication
from toolpermit.config import (
    DEFAULT_CONFIG_NAME,
    ConfigError,
    Settings,
    load_settings,
    starter_config,
    starter_policy,
)
from toolpermit.policy import PolicyLoadError, load_policy
from toolpermit.protocol.mcp.proxy import ProxyConfig, run_proxy
from toolpermit.web import run_ui, validate_loopback_host


class ExitCode(IntEnum):
    OK = 0
    CONFIGURATION = 3
    CONFLICT_OR_NOT_FOUND = 4
    REGRESSION = 5


app = typer.Typer(
    no_args_is_help=True,
    invoke_without_command=True,
    help="Local permission policies for MCP tool calls.",
)
policy_app = typer.Typer(no_args_is_help=True, help="Generate and validate policy candidates.")
approvals_app = typer.Typer(no_args_is_help=True, help="Review pending local approvals.")
runs_app = typer.Typer(no_args_is_help=True, help="Inspect recorded proxy runs.")
audit_app = typer.Typer(no_args_is_help=True, help="Export or delete redacted audit data.")
config_app = typer.Typer(no_args_is_help=True, help="Inspect effective configuration.")
app.add_typer(policy_app, name="policy")
app.add_typer(approvals_app, name="approvals")
app.add_typer(runs_app, name="runs")
app.add_typer(audit_app, name="audit")
app.add_typer(config_app, name="config")


def _fail(message: str, code: ExitCode) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(int(code))


def _settings(config_path: Path | None) -> Settings:
    try:
        return load_settings(config_path)
    except ConfigError as error:
        _fail(str(error), ExitCode.CONFIGURATION)


def _application(config_path: Path | None, database: Path | None = None) -> ToolPermitApplication:
    settings = _settings(config_path)
    return ToolPermitApplication(database or settings.database)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


@app.callback()
def main(
    version: Annotated[
        bool, typer.Option("--version", help="Show the ToolPermit version.")
    ] = False,
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def init(
    config: Annotated[
        Path, typer.Option("--config", help="Configuration file to create.")
    ] = Path(DEFAULT_CONFIG_NAME),
    policy: Annotated[
        Path | None, typer.Option("--policy", help="Starter policy file to create.")
    ] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite both target files.")] = False,
) -> None:
    """Create a documented local configuration and approval-first policy."""
    policy_path = policy or config.parent / "toolpermit.yaml"
    existing = [path for path in (config, policy_path) if path.exists()]
    if existing and not force:
        _fail(
            "refusing to overwrite: " + ", ".join(str(path) for path in existing),
            ExitCode.CONFLICT_OR_NOT_FOUND,
        )
    config.parent.mkdir(parents=True, exist_ok=True)
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    configured_policy = str(policy_path.resolve()) if policy is not None else "toolpermit.yaml"
    config.write_text(starter_config(policy=configured_policy), encoding="utf-8")
    policy_path.write_text(starter_policy(), encoding="utf-8")
    typer.echo(f"Created {config} and {policy_path}.")
    typer.echo("Start with observe mode; enforce mode applies the approval-first policy.")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def wrap(
    ctx: typer.Context,
    mode: Annotated[str, typer.Option(help="Proxy mode: observe or enforce.")] = "observe",
    config: Annotated[Path | None, typer.Option("--config")] = None,
    policy: Annotated[Path | None, typer.Option("--policy")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    approval_ttl: Annotated[float | None, typer.Option("--approval-ttl")] = None,
) -> None:
    """Wrap an MCP stdio server command after `--`."""
    if mode not in {"observe", "enforce"}:
        _fail("--mode must be observe or enforce", ExitCode.CONFIGURATION)
    command = tuple(ctx.args)
    if not command:
        _fail("an upstream command is required after --", ExitCode.CONFIGURATION)
    settings = _settings(config)
    selected_policy = policy or settings.policy
    loaded_policy = None
    if mode == "enforce":
        try:
            loaded_policy = load_policy(selected_policy)
        except PolicyLoadError as error:
            _fail(str(error), ExitCode.CONFIGURATION)
    else:
        typer.echo("WARNING: observe mode records calls but does not enforce policy.", err=True)
    proxy = ProxyConfig(
        mode=mode,
        database=database or settings.database,
        command=command,
        policy=loaded_policy,
        approval_ttl=approval_ttl or settings.approval_ttl,
    )
    raise typer.Exit(asyncio.run(run_proxy(proxy)))


@policy_app.command("suggest")
def policy_suggest(
    from_run: Annotated[str, typer.Option("--from-run", help="Evidence run ID.")],
    output: Annotated[Path, typer.Option("--output", help="Inactive policy candidate path.")],
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    """Generate an inactive, deterministic policy candidate."""
    if output.exists() and not force:
        _fail(f"refusing to overwrite: {output}", ExitCode.CONFLICT_OR_NOT_FOUND)
    suggestion = _application(config, database).suggest(from_run)
    if not suggestion.evidence_event_ids:
        _fail(f"run has no events: {from_run}", ExitCode.CONFLICT_OR_NOT_FOUND)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(suggestion.content, encoding="utf-8")
    typer.echo(
        f"Wrote inactive candidate {output} from "
        f"{len(suggestion.evidence_event_ids)} event(s)."
    )
    for warning in suggestion.warnings:
        typer.echo(f"WARNING: {warning}", err=True)


@app.command()
def replay(
    policy: Annotated[Path, typer.Option("--policy", help="Candidate policy.")],
    baseline: Annotated[Path | None, typer.Option("--baseline")] = None,
    run: Annotated[str | None, typer.Option("--run")] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit versioned JSON.")] = False,
    fail_on_change: Annotated[bool, typer.Option("--fail-on-change")] = False,
) -> None:
    """Evaluate stored calls offline without starting an upstream process."""
    try:
        report = _application(config, database).replay(policy, run_id=run, baseline_path=baseline)
    except PolicyLoadError as error:
        _fail(str(error), ExitCode.CONFIGURATION)
    payload = {
        "schema_version": report.schema_version,
        "counts": report.counts(),
        "items": [
            {
                "event_id": item.event_id,
                "baseline": item.baseline.value if item.baseline is not None else None,
                "candidate": item.candidate.value,
                "transition": item.transition,
                "baseline_rule_id": item.baseline_rule_id,
                "candidate_rule_id": item.candidate_rule_id,
                "indeterminate": item.indeterminate,
                "diagnostics": list(item.diagnostics),
            }
            for item in report.items
        ],
    }
    if json_output:
        typer.echo(_json(payload))
    else:
        typer.echo("Transition counts:")
        for name, count in report.counts().items():
            typer.echo(f"  {name}: {count}")
        for item in report.items:
            baseline_name = item.baseline.value if item.baseline is not None else "none"
            typer.echo(
                f"{item.event_id}: {baseline_name} -> "
                f"{item.candidate.value} [{item.transition}]"
            )
    changed = any(item.transition not in {"unchanged", "evaluated"} for item in report.items)
    if fail_on_change and changed:
        raise typer.Exit(int(ExitCode.REGRESSION))


@approvals_app.command("list")
def approvals_list(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List pending approvals with redacted event details."""
    application = _application(config, database)
    values: list[dict[str, object]] = []
    for approval in application.list_pending_approvals():
        event = application.get_event(approval.event_id)
        values.append(
            {
                "id": approval.id,
                "state": approval.state.value,
                "expires_at": approval.expires_at,
                "event_id": event.id,
                "tool_name": event.tool_name,
                "arguments": event.arguments,
                "redacted_paths": list(event.redacted_paths),
                "rule_id": event.rule_id,
                "connection_id": event.connection_id,
            }
        )
    if json_output:
        typer.echo(_json({"schema_version": 1, "approvals": values}))
    elif not values:
        typer.echo("No pending approvals.")
    else:
        for item in values:
            typer.echo(f"{item['id']}  {item['tool_name']}  rule={item['rule_id']}")
            typer.echo(json.dumps(item["arguments"], ensure_ascii=False, sort_keys=True))


def _decide(approval_id: str, *, approve: bool, config: Path | None, database: Path | None) -> None:
    application = _application(config, database)
    changed = (
        application.approve(approval_id, actor="local-cli")
        if approve
        else application.reject(approval_id, actor="local-cli")
    )
    if not changed:
        _fail("approval is missing, expired, or no longer pending", ExitCode.CONFLICT_OR_NOT_FOUND)
    typer.echo(f"{approval_id}: {'approved' if approve else 'rejected'}")


@approvals_app.command("approve")
def approvals_approve(
    approval_id: str,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Approve one exact pending call."""
    _decide(approval_id, approve=True, config=config, database=database)


@approvals_app.command("reject")
def approvals_reject(
    approval_id: str,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Reject a pending call."""
    _decide(approval_id, approve=False, config=config, database=database)


@runs_app.command("list")
def runs_list(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List recorded runs newest first."""
    values: list[dict[str, object]] = []
    for run in _application(config, database).list_runs():
        value: dict[str, object] = {
            "id": run.id,
            "mode": run.mode,
            "started_at": run.started_at,
            "ended_at": run.ended_at,
            "upstream_command": list(run.upstream_command),
        }
        values.append(value)
    if json_output:
        typer.echo(_json({"schema_version": 1, "runs": values}))
    elif not values:
        typer.echo("No recorded runs.")
    else:
        for value in values:
            ended = "finished" if value["ended_at"] is not None else "active"
            typer.echo(f"{value['id']}  {value['mode']}  {ended}")


@runs_app.command("show")
def runs_show(
    run_id: str,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show redacted events from one run."""
    events = _application(config, database).events_for_run(run_id)
    values = [
        {
            "id": event.id,
            "tool_name": event.tool_name,
            "arguments": event.arguments,
            "redacted_paths": list(event.redacted_paths),
            "decision": event.decision.value,
            "rule_id": event.rule_id,
            "lifecycle": event.lifecycle,
        }
        for event in events
    ]
    if json_output:
        typer.echo(_json({"schema_version": 1, "run_id": run_id, "events": values}))
    elif not values:
        typer.echo(f"Run {run_id} has no events.")
    else:
        for value in values:
            typer.echo(
                f"{value['id']}  {value['tool_name']}  "
                f"{value['decision']}  {value['lifecycle']}"
            )


@audit_app.command("export")
def audit_export(
    format_name: Annotated[str, typer.Option("--format")] = "jsonl",
    run: Annotated[str | None, typer.Option("--run")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Export deterministic redacted audit records."""
    if format_name != "jsonl":
        _fail("only jsonl export is supported in v0.1", ExitCode.CONFIGURATION)
    content = "\n".join(_application(config, database).export_jsonl(run_id=run))
    if content:
        content += "\n"
    if output is None:
        typer.echo(content, nl=False)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        typer.echo(f"Exported redacted audit data to {output}.")


@audit_app.command("delete")
def audit_delete(
    run_id: str,
    yes: Annotated[bool, typer.Option("--yes", help="Confirm permanent deletion.")] = False,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
) -> None:
    """Permanently delete one run and its associated records."""
    if not yes:
        _fail("pass --yes to confirm permanent deletion", ExitCode.CONFLICT_OR_NOT_FOUND)
    if not _application(config, database).delete_run(run_id):
        _fail(f"run not found: {run_id}", ExitCode.CONFLICT_OR_NOT_FOUND)
    typer.echo(f"Deleted run {run_id}; this cannot be recovered from ToolPermit.")


@config_app.command("show")
def config_show(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show resolved effective configuration (no secrets are stored)."""
    settings = _settings(config)
    payload = {
        "schema_version": 1,
        "database": str(settings.database),
        "policy": str(settings.policy),
        "approval_ttl": settings.approval_ttl,
        "ui": {"host": settings.ui.host, "port": settings.ui.port},
    }
    typer.echo(_json(payload) if json_output else json.dumps(payload, indent=2, ensure_ascii=False))


@app.command("ui")
def ui_command(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    database: Annotated[Path | None, typer.Option("--database")] = None,
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
) -> None:
    """Serve the local approval UI on a loopback address."""
    settings = _settings(config)
    selected_host = host or settings.ui.host
    selected_port = port or settings.ui.port
    try:
        validate_loopback_host(selected_host)
    except ValueError as error:
        _fail(str(error), ExitCode.CONFIGURATION)
    typer.echo(f"ToolPermit UI: http://{selected_host}:{selected_port}")
    run_ui(database or settings.database, host=selected_host, port=selected_port)
