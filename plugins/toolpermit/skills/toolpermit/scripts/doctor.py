#!/usr/bin/env python3
"""Read-only environment check for the ToolPermit Codex skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SUPPORTED_MIN = (3, 11)
SUPPORTED_MAX = (3, 13)


def _toolpermit_executable() -> Path | None:
    name = "toolpermit.exe" if sys.platform == "win32" else "toolpermit"
    sibling = Path(sys.executable).resolve().parent / name
    if sibling.is_file():
        return sibling
    discovered = shutil.which("toolpermit")
    return Path(discovered).resolve() if discovered else None


def _toolpermit_status(executable: Path | None) -> dict[str, object]:
    if executable is None:
        return {"installed": False, "executable": None, "version": None, "error": None}
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "installed": True,
            "executable": str(executable),
            "version": None,
            "error": str(error),
        }
    version = result.stdout.strip() if result.returncode == 0 else None
    error = result.stderr.strip() or None if result.returncode != 0 else None
    return {
        "installed": True,
        "executable": str(executable),
        "version": version,
        "error": error,
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("toolpermit.config.yaml"))
    parser.add_argument("--policy", type=Path, default=Path("toolpermit.yaml"))
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    version = sys.version_info[:2]
    python_supported = SUPPORTED_MIN <= version <= SUPPORTED_MAX
    toolpermit = _toolpermit_status(_toolpermit_executable())
    guidance: list[str] = []
    if not python_supported:
        guidance.append("Select Python 3.11, 3.12, or 3.13 for ToolPermit.")
    if not toolpermit["installed"]:
        guidance.append(
            'Create a project virtual environment, then install "toolpermit>=0.1,<0.2".'
        )
    elif toolpermit["error"]:
        guidance.append("The ToolPermit executable exists but did not return a version.")
    if arguments.config.exists() != arguments.policy.exists():
        guidance.append("Only one expected ToolPermit file exists; inspect before initializing.")

    payload = {
        "schema_version": 1,
        "python": {
            "executable": str(Path(sys.executable).resolve()),
            "version": ".".join(str(part) for part in sys.version_info[:3]),
            "supported": python_supported,
        },
        "toolpermit": toolpermit,
        "project": {
            "directory": str(Path.cwd().resolve()),
            "config": str(arguments.config.resolve()),
            "config_exists": arguments.config.is_file(),
            "policy": str(arguments.policy.resolve()),
            "policy_exists": arguments.policy.is_file(),
        },
        "guidance": guidance,
    }
    if arguments.json_output:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        python_state = "ok" if python_supported else "unsupported"
        print(f"Python {payload['python']['version']}: {python_state}")
        installed = toolpermit["installed"] and not toolpermit["error"]
        print(f"ToolPermit: {toolpermit['version'] if installed else 'not ready'}")
        print(f"Config: {'found' if arguments.config.is_file() else 'not found'}")
        print(f"Policy: {'found' if arguments.policy.is_file() else 'not found'}")
        for item in guidance:
            print(f"Next: {item}")
    if not python_supported:
        return 2
    return 0 if toolpermit["installed"] and not toolpermit["error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
