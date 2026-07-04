from unittest.mock import MagicMock, patch

import pytest

from cli.runner import run_playbook


@patch("cli.runner.ansible_runner.run")
def test_runner_success(mock_run):
    mock_run.return_value = MagicMock(rc=0)

    run_playbook(
        "discover",
        "router1",
        {},
    )

    mock_run.assert_called_once()


@patch("cli.runner.ansible_runner.run")
def test_runner_fail(mock_run):
    mock_run.return_value = MagicMock(rc=1)

    with pytest.raises(SystemExit):
        run_playbook(
            "discover",
            "router1",
            {},
        )