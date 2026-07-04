from unittest.mock import patch

import typer

from cli.commands.discover import discover


class DummyContext:
    invoked_subcommand = None


@patch("cli.commands.discover.run_playbook")
def test_discover(mock_run):
    discover(DummyContext())

    mock_run.assert_called_once_with(
        "discover",
        "all",
        {},
    )