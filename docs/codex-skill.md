# ToolPermit Codex Skill

The ToolPermit Codex Skill turns the project's observe-first MCP permission workflow into a
repeatable Codex capability. It can check or install the Python package, wrap an existing local MCP
stdio server, review policies, manage exact approvals, inspect redacted audit records, and diagnose
configuration problems.

The Skill does not grant Codex permission to approve tool calls automatically. It also does not turn
ToolPermit into an operating-system sandbox or add support for remote MCP transports.

## Install from GitHub

Requirements:

- A current Codex release with the `codex plugin` command.
- Python 3.11, 3.12, or 3.13 for the ToolPermit package.

Add this repository as a marketplace, then install the plugin:

```bash
codex plugin marketplace add sunhao123456sun-svg/toolpermit --ref main
codex plugin add toolpermit@toolpermit
```

The `main` reference follows the latest reviewed repository state. To pin this release for a
reproducible installation, use:

```bash
codex plugin marketplace add sunhao123456sun-svg/toolpermit --ref v0.1.1
codex plugin add toolpermit@toolpermit
```

Start a new Codex task after installation so the Skill is discovered. Invoke it explicitly with a
request such as:

```text
Use $toolpermit to install ToolPermit in this project and safely wrap this MCP stdio server in
observe mode: npx -y @modelcontextprotocol/server-filesystem ./workspace
```

Codex can also select the Skill implicitly for requests about configuring ToolPermit, wrapping an
MCP stdio server, reviewing ToolPermit policy, approvals, replay, redacted audit, or troubleshooting.

## What the Skill will do

1. Inspect Python, the ToolPermit CLI, existing config, and the original MCP command.
2. Propose a project virtual environment when installation is needed.
3. Create config without overwriting existing files.
4. Show the intended MCP client change before writing it.
5. Start in observe mode and verify a contained interaction.
6. Suggest and replay a candidate policy from redacted evidence.
7. Enter enforce mode only after policy review and explicit user direction.
8. Leave the original MCP command as the rollback path.

The bundled doctor is read-only. From a checkout, run it directly with:

```bash
python plugins/toolpermit/skills/toolpermit/scripts/doctor.py --json
```

## Update

Refresh the Git marketplace snapshot, then reinstall the plugin:

```bash
codex plugin marketplace upgrade toolpermit
codex plugin add toolpermit@toolpermit
```

Start a new task after updating.

If the marketplace was pinned to a release tag, remove it and add the desired newer tag before
reinstalling. Release tags are intentionally immutable and do not advance when `marketplace
upgrade` is run.

## Remove

Remove the installed plugin and, if no longer needed, its marketplace source:

```bash
codex plugin remove toolpermit@toolpermit
codex plugin marketplace remove toolpermit
```

Removing the Codex Plugin does not uninstall the Python package or delete ToolPermit configuration,
policies, or audit data.

## Develop from a checkout

Codex scans `.agents/skills` from a repository root. This repository exposes the same canonical
Skill there for local development, so opening the checkout in Codex makes `$toolpermit` available
without installing the Plugin.

Validate the distributable files with:

```bash
python scripts/check_codex_plugin.py
```

The repository CI also validates the Skill, plugin manifest, marketplace metadata, local discovery
link, and doctor output.
