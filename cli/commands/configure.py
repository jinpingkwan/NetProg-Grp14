import glob
import ipaddress
from pathlib import Path
from typing import Optional

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

import typer

from cli.runner import PROJECT_ROOT, run_playbook

app = typer.Typer(no_args_is_help=True, help="Configure a network device")


def _validate_ipv4(value: str) -> str:
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        raise typer.BadParameter(f"'{value}' is not a valid IPv4 address")
    return value


def _validate_mask(value: str) -> str:
    try:
        ipaddress.IPv4Network(f"0.0.0.0/{value}")
    except ValueError:
        raise typer.BadParameter(f"'{value}' is not a valid subnet mask")
    return value


def _validate_network(value: str) -> str:
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError:
        raise typer.BadParameter(
            f"'{value}' is not a valid CIDR prefix (e.g. 10.0.0.0/24)"
        )
    return value


@app.command("ip")
def set_ip(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
    ip: Annotated[
        str,
        typer.Option(
            help="IPv4 address to assign",
            callback=_validate_ipv4,
        ),
    ],
    mask: Annotated[
        str,
        typer.Option(
            help="Subnet mask (dotted decimal)",
            callback=_validate_mask,
        ),
    ],
    iface: Annotated[
        Optional[str],
        typer.Option(
            help="Interface name (e.g. GigabitEthernet3); defaults to the router's default_data_interface"
        ),
    ] = None,
) -> None:
    """Configure an IP address on a network device interface."""

    prefix_length = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen

    extra_vars = {
        "ip_address": ip,
        "subnet_mask": mask,
        "prefix_length": prefix_length,
    }

    if iface is not None:
        extra_vars["interface_name"] = iface

    run_playbook("configure_ip", host, extra_vars)


@app.command("user")
def create_user(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
    username: Annotated[str, typer.Option(help="Username to create")],
    password: Annotated[
        str,
        typer.Option(
            prompt=True,
            hide_input=True,
            confirmation_prompt=True,
            help="Password for the new user",
        ),
    ] = "",
) -> None:
    """Create a user account on a network device."""

    run_playbook(
        "configure_user",
        host,
        {
            "new_username": username,
            "new_password": password,
        },
    )


@app.command("baseline")
def configure_baseline(
    host: Annotated[
        str,
        typer.Argument(help="Inventory hostname of the target device"),
    ],
    username: Annotated[
        str,
        typer.Option(help="Username to create"),
    ],
    password: Annotated[
        str,
        typer.Option(
            prompt=True,
            hide_input=True,
            confirmation_prompt=True,
            help="Password for the new user",
        ),
    ] = "",
) -> None:
    """
    Configure a complete baseline on a freshly deployed router.
    Applies interface configuration, user account, banner,
    and static routes using playbook.yml.
    """

    run_playbook(
        "playbook",
        host,
        {
            "new_username": username,
            "new_password": password,
        },
    )


@app.command("banner")
def set_banner(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
    message: Annotated[
        str,
        typer.Option(help="Banner text to display at login"),
    ],
) -> None:
    """Set a login banner message on a network device."""

    run_playbook(
        "configure_banner",
        host,
        {
            "banner_message": message,
        },
    )


@app.command("interface")
def set_interface(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
    iface: Annotated[
        str,
        typer.Option(help="Interface name (e.g. Gi0/1)"),
    ],
    desc: Annotated[
        str,
        typer.Option(help="Description to set on the interface"),
    ],
) -> None:
    """Set a description on a network device interface."""

    run_playbook(
        "configure_interface",
        host,
        {
            "interface_name": iface,
            "interface_desc": desc,
        },
    )


@app.command("route")
def add_route(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
    dest: Annotated[
        str,
        typer.Option(
            help="Destination network in CIDR notation (e.g. 10.0.0.0/24)",
            callback=_validate_network,
        ),
    ],
    via: Annotated[
        str,
        typer.Option(
            help="Next-hop gateway IPv4 address",
            callback=_validate_ipv4,
        ),
    ],
) -> None:
    """Add a static route on a network device."""

    run_playbook(
        "configure_route",
        host,
        {
            "route_dest": dest,
            "route_gateway": via,
        },
    )


@app.command("backup")
def backup(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
) -> None:
    """Back up a device's running-config to the control node."""

    run_playbook("backup_config", host, {})


def _latest_backup(host: str) -> str:
    candidates = sorted(glob.glob(str(PROJECT_ROOT / "backups" / f"{host}_*.cfg")))
    if not candidates:
        raise typer.BadParameter(
            f"No backups found for '{host}' under backups/; run "
            f"'netauto configure backup {host}' first or pass --file explicitly"
        )
    return str(Path(candidates[-1]).relative_to(PROJECT_ROOT))


@app.command("restore")
def restore(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target device")],
    file: Annotated[
        Optional[str],
        typer.Option(
            "--file",
            help="Path to a backup file under backups/; defaults to the most recent backup for this host",
        ),
    ] = None,
) -> None:
    """Restore a device's config from a previously captured backup."""

    backup_file = file or _latest_backup(host)

    run_playbook(
        "restore_config",
        host,
        {"backup_file": backup_file},
    )