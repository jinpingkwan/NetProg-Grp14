from unittest.mock import patch

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


@patch("cli.commands.configure.run_playbook")
def test_configure_ip(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "ip",
            "router1",
            "--ip",
            "192.168.1.1",
            "--mask",
            "255.255.255.0",
            "--iface",
            "GigabitEthernet1",
        ],
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "configure_ip",
        "router1",
        {
            "ip_address": "192.168.1.1",
            "subnet_mask": "255.255.255.0",
            "prefix_length": 24,
            "interface_name": "GigabitEthernet1",
        },
    )


@patch("cli.commands.configure.run_playbook")
def test_configure_ip_rejects_bad_ip(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "ip",
            "router1",
            "--ip",
            "999.1.1.1",
            "--mask",
            "255.255.255.0",
        ],
    )

    assert result.exit_code != 0
    mock_run.assert_not_called()


@patch("cli.commands.configure.run_playbook")
def test_configure_ip_rejects_bad_mask(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "ip",
            "router1",
            "--ip",
            "192.168.1.1",
            "--mask",
            "255.255.255.7",
        ],
    )

    assert result.exit_code != 0
    mock_run.assert_not_called()


@patch("cli.commands.configure.run_playbook")
def test_configure_route(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "route",
            "router1",
            "--dest",
            "10.0.0.0/24",
            "--via",
            "192.168.1.1",
        ],
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "configure_route",
        "router1",
        {
            "route_dest": "10.0.0.0/24",
            "route_gateway": "192.168.1.1",
        },
    )


@patch("cli.commands.configure.run_playbook")
def test_configure_route_rejects_bad_dest(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "route",
            "router1",
            "--dest",
            "not-a-network",
            "--via",
            "192.168.1.1",
        ],
    )

    assert result.exit_code != 0
    mock_run.assert_not_called()


@patch("cli.commands.configure.run_playbook")
def test_configure_route_rejects_bad_gateway(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "route",
            "router1",
            "--dest",
            "10.0.0.0/24",
            "--via",
            "not-an-ip",
        ],
    )

    assert result.exit_code != 0
    mock_run.assert_not_called()


@patch("cli.commands.configure.run_playbook")
def test_configure_user_prompt(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "user",
            "router1",
            "--username",
            "admin",
        ],
        input="secret123\nsecret123\n",
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "configure_user",
        "router1",
        {
            "new_username": "admin",
            "new_password": "secret123",
        },
    )


@patch("cli.commands.configure.run_playbook")
def test_configure_user_password_mismatch(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "user",
            "router1",
            "--username",
            "admin",
        ],
        input="secret123\nwrong\n",
    )

    assert "repeat for confirmation" in result.output.lower() or \
           "error" in result.output.lower() or \
           "match" in result.output.lower()