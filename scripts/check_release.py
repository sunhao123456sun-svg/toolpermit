"""Fail when release metadata, docs, or package-critical files disagree."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "CHANGELOG.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SUPPORT.md",
    "ROADMAP.md",
    "docs/quickstart.md",
    "docs/codex-skill.md",
    "docs/cli-reference.md",
    "docs/configuration.md",
    "docs/policy-reference.md",
    "docs/security.md",
    "docs/privacy.md",
    "docs/troubleshooting.md",
    "docs/limitations.md",
    "examples/demo_client.py",
    "examples/demo_server.py",
    "benchmarks/benchmark_policy.py",
    "benchmarks/README.md",
    "plugins/toolpermit/.codex-plugin/plugin.json",
    "plugins/toolpermit/skills/toolpermit/SKILL.md",
)


def _project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        document = tomllib.load(handle)
    return str(document["project"]["version"])


def _module_version() -> str:
    text = (ROOT / "src/toolpermit/__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__ = "([^"]+)"$', text, re.MULTILINE)
    if match is None:
        raise AssertionError("cannot locate __version__")
    return match.group(1)


def _markdown_links(path: Path) -> tuple[Path, ...]:
    text = path.read_text(encoding="utf-8")
    links = re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", text)
    resolved: list[Path] = []
    for target in links:
        clean = target.split("#", 1)[0]
        if not clean or "://" in clean or clean.startswith("mailto:"):
            continue
        resolved.append((path.parent / clean).resolve())
    return tuple(resolved)


def main() -> int:
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if missing:
        raise AssertionError("missing required release files: " + ", ".join(missing))
    project_version = _project_version()
    module_version = _module_version()
    if project_version != module_version:
        raise AssertionError(
            f"version mismatch: pyproject={project_version}, module={module_version}"
        )
    markdown = tuple(ROOT.glob("*.md")) + tuple((ROOT / "docs").glob("*.md"))
    broken: list[str] = []
    for document in markdown:
        for target in _markdown_links(document):
            if not target.exists():
                broken.append(f"{document.relative_to(ROOT)} -> {target}")
    if broken:
        raise AssertionError("broken local Markdown links:\n" + "\n".join(broken))
    print(f"release metadata and local documentation links: ok (v{project_version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
