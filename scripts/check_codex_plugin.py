"""Validate the repository's distributable Codex Skill and plugin metadata."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "toolpermit"
SKILL = PLUGIN / "skills" / "toolpermit"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
REPO_SKILL = ROOT / ".agents" / "skills" / "toolpermit"


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError(f"{name} must be an object")
    return cast(dict[str, object], value)


def _load_json(path: Path) -> dict[str, object]:
    return _object(json.loads(path.read_text(encoding="utf-8")), str(path))


def _frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"missing YAML frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise AssertionError(f"unterminated YAML frontmatter: {path}") from error
    values: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if not separator or not value.strip():
            raise AssertionError(f"invalid frontmatter line: {line!r}")
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    required = (
        MANIFEST,
        MARKETPLACE,
        SKILL / "SKILL.md",
        SKILL / "agents" / "openai.yaml",
        SKILL / "scripts" / "doctor.py",
        SKILL / "references" / "commands.md",
        ROOT / "docs" / "codex-skill.md",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise AssertionError("missing Codex distribution files: " + ", ".join(missing))

    manifest = _load_json(MANIFEST)
    if manifest.get("name") != "toolpermit" or manifest.get("version") != "0.1.0":
        raise AssertionError("plugin name/version mismatch")
    if manifest.get("skills") != "./skills/":
        raise AssertionError("plugin skills path mismatch")
    interface = _object(manifest.get("interface"), "plugin interface")
    for name in ("displayName", "shortDescription", "longDescription", "developerName"):
        if not interface.get(name):
            raise AssertionError(f"missing plugin interface field: {name}")

    marketplace = _load_json(MARKETPLACE)
    if marketplace.get("name") != "toolpermit":
        raise AssertionError("marketplace name mismatch")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        raise AssertionError("marketplace must contain exactly one plugin")
    entry = _object(entries[0], "marketplace plugin")
    source = _object(entry.get("source"), "marketplace source")
    if entry.get("name") != "toolpermit" or source.get("path") != "./plugins/toolpermit":
        raise AssertionError("marketplace source mismatch")
    policy = _object(entry.get("policy"), "marketplace policy")
    if policy != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}:
        raise AssertionError("marketplace policy mismatch")

    frontmatter = _frontmatter(SKILL / "SKILL.md")
    if set(frontmatter) != {"name", "description"} or frontmatter["name"] != "toolpermit":
        raise AssertionError(
            "skill frontmatter must contain only the expected name and description"
        )
    if len(frontmatter["description"]) < 120:
        raise AssertionError("skill trigger description is not specific enough")
    expected_triggers = (
        "MCP stdio",
        "wrap",
        "allow/ask/deny",
        "approvals",
        "replay",
        "redacted audit",
        "troubleshoot",
        "remote MCP transports",
    )
    for trigger in expected_triggers:
        if trigger not in frontmatter["description"]:
            raise AssertionError(f"skill description is missing trigger or boundary: {trigger}")

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    plugin_text = MANIFEST.read_text(encoding="utf-8")
    if "[TODO:" in skill_text or "[TODO:" in plugin_text:
        raise AssertionError("Codex distribution contains a TODO placeholder")
    agent_metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "$toolpermit" not in agent_metadata:
        raise AssertionError("default prompt must explicitly invoke $toolpermit")
    if not REPO_SKILL.is_symlink() or REPO_SKILL.resolve() != SKILL.resolve():
        raise AssertionError("repo-local ToolPermit skill link is missing or incorrect")

    installation = (ROOT / "docs" / "codex-skill.md").read_text(encoding="utf-8")
    install_commands = (
        "codex plugin marketplace add sunhao123456sun-svg/toolpermit --ref main",
        "codex plugin add toolpermit@toolpermit",
    )
    for command in install_commands:
        if command not in installation:
            raise AssertionError(f"Codex installation guide is missing: {command}")

    doctor = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "doctor.py"), "--json"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if doctor.returncode not in {0, 1, 2}:
        raise AssertionError(f"doctor failed unexpectedly: {doctor.stderr}")
    payload = _object(json.loads(doctor.stdout), "doctor output")
    if payload.get("schema_version") != 1:
        raise AssertionError("doctor schema mismatch")

    print("Codex Skill, plugin, marketplace, repo discovery, and doctor: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
