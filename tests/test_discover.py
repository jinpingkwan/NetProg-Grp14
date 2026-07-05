from unittest.mock import patch

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@patch("cli.commands.discover.run_playbook")
def test_discover(mock_run):
    result = runner.invoke(app, ["discover"])

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "discover",
        "all",
        {},
    )