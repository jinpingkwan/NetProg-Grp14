from unittest.mock import patch

from cli.commands.info import device_info, system_info


@patch("cli.commands.info.run_playbook")
def test_device_info(mock_run):
    device_info("router1")

    mock_run.assert_called_once_with(
        "info_device",
        "router1",
        {},
    )


@patch("cli.commands.info.run_playbook")
def test_system_info(mock_run):
    system_info(
        "server1",
        host_ip="172.20.20.21",
    )

    mock_run.assert_called_once_with(
        "info_system",
        "server1",
        {
            "ansible_host": "172.20.20.21",
        },
    )


@patch("cli.commands.info.run_playbook")
def test_system_info_without_host(mock_run):
    system_info("server1")

    mock_run.assert_called_once_with(
        "info_system",
        "server1",
        {},
    )