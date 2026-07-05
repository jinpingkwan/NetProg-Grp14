from unittest.mock import patch

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@patch("cli.commands.info.run_playbook")
def test_device_info(mock_run):
    result = runner.invoke(app, ["info", "device", "router1"])

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "info_device",
        "router1",
        {},
    )


@patch("cli.commands.info.run_playbook")
def test_system_info(mock_run):
    result = runner.invoke(app, ["info", "system", "server1"])

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "info_system",
        "server1",
        {},
    )


@patch("cli.commands.info.run_playbook")
def test_system_info_override_host(mock_run):
    result = runner.invoke(
        app,
        [
            "info",
            "system",
            "server1",
            "--host",
            "172.20.20.21",
        ],
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "info_system",
        "server1",
        {
            "ansible_host": "172.20.20.21",
        },
    )