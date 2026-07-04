from unittest.mock import patch

from cli.commands.configure import (
    set_ip,
    create_user,
    set_banner,
    set_interface,
    add_route,
)


@patch("cli.commands.configure.run_playbook")
def test_set_ip(mock_run):
    set_ip(
        host="router1",
        ip="192.168.1.1",
        mask="255.255.255.0",
        iface="GigabitEthernet1",
    )

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
def test_create_user(mock_run):
    create_user(
        host="router1",
        username="netadmin",
        password="password123",
    )

    mock_run.assert_called_once_with(
        "configure_user",
        "router1",
        {
            "new_username": "netadmin",
            "new_password": "password123",
        },
    )


@patch("cli.commands.configure.run_playbook")
def test_set_banner(mock_run):
    set_banner(
        host="router1",
        message="Authorized Access Only",
    )

    mock_run.assert_called_once_with(
        "configure_banner",
        "router1",
        {"banner_message": "Authorized Access Only"},
    )


@patch("cli.commands.configure.run_playbook")
def test_set_interface(mock_run):
    set_interface(
        host="router1",
        iface="GigabitEthernet1",
        desc="Connected to Switch",
    )

    mock_run.assert_called_once_with(
        "configure_interface",
        "router1",
        {
            "interface_name": "GigabitEthernet1",
            "interface_desc": "Connected to Switch",
        },
    )


@patch("cli.commands.configure.run_playbook")
def test_add_route(mock_run):
    add_route(
        host="router1",
        dest="10.10.10.0/24",
        via="192.168.1.254",
    )

    mock_run.assert_called_once_with(
        "configure_route",
        "router1",
        {
            "route_dest": "10.10.10.0/24",
            "route_gateway": "192.168.1.254",
        },
    )