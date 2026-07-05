from unittest.mock import patch
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

# ==========================================================
# IP CONFIGURATION TESTS
# ==========================================================

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
def test_configure_ip_without_iface(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "ip",
            "router1",
            "--ip",
            "192.168.1.10",
            "--mask",
            "255.255.255.0",
        ],
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "configure_ip",
        "router1",
        {
            "ip_address": "192.168.1.10",
            "subnet_mask": "255.255.255.0",
            "prefix_length": 24,
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


# ==========================================================
# USER CONFIGURATION TESTS
# ==========================================================

@patch("cli.commands.configure.run_playbook")
def test_configure_user_success(mock_run):
    result = runner.invoke(
        app,
        ["configure", "user", "router1", "--username", "admin"],
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
        ["configure", "user", "router1", "--username", "admin"],
        input="secret123\nwrong123\n",
    )

    assert result.exit_code != 0
    mock_run.assert_not_called()


# ==========================================================
# BANNER TEST (FIXED MISSING COVERAGE)
# ==========================================================

@patch("cli.commands.configure.run_playbook")
def test_configure_banner(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "banner",
            "router1",
            "--message",
            "Hello Network",
        ],
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "configure_banner",
        "router1",
        {"banner_message": "Hello Network"},
    )


# ==========================================================
# INTERFACE TEST (FIXED MISSING COVERAGE)
# ==========================================================

@patch("cli.commands.configure.run_playbook")
def test_configure_interface(mock_run):
    result = runner.invoke(
        app,
        [
            "configure",
            "interface",
            "router1",
            "--iface",
            "GigabitEthernet3",
            "--desc",
            "Uplink Port",
        ],
    )

    assert result.exit_code == 0

    mock_run.assert_called_once_with(
        "configure_interface",
        "router1",
        {
            "interface_name": "GigabitEthernet3",
            "interface_desc": "Uplink Port",
        },
    )