from typer.testing import CliRunner

from toolpermit import __version__
from toolpermit.cli import app


def test_version_without_subcommand() -> None:
    result = CliRunner().invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__

