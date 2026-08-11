from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from toolpermit.audit import AuditStore

ROOT = Path(__file__).resolve().parents[2]


def test_documented_observe_demo_is_contained_and_records_event(tmp_path: Path) -> None:
    demo_dir = tmp_path / "demo-workspace"
    database = tmp_path / "audit.db"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "demo_client.py"),
            "--mode",
            "observe",
            "--demo-dir",
            str(demo_dir),
            "--database",
            str(database),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (demo_dir / "output.txt").read_text(encoding="utf-8") == (
        "ToolPermit contained demo completed.\n"
    )
    events = AuditStore(database).list_events()
    assert len(events) == 1
    assert events[0].tool_name == "write_demo"
    assert events[0].redacted_paths == ("token",)
    assert "demo-placeholder" not in database.read_text(encoding="utf-8", errors="ignore")


def test_demo_server_rejects_path_escape(tmp_path: Path) -> None:
    demo_dir = tmp_path / "contained"
    outside = tmp_path / "outside.txt"
    code = (
        "import os; "
        f"os.environ['TOOLPERMIT_DEMO_DIR']={str(demo_dir)!r}; "
        "from examples.demo_server import write_demo; "
        "write_demo('../outside.txt', 'unsafe')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode != 0
    assert "escapes TOOLPERMIT_DEMO_DIR" in result.stderr
    assert not outside.exists()
