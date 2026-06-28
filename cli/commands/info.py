from typing import Annotated, Optional

import typer

from cli.runner import run_playbook

app = typer.Typer(no_args_is_help=True, help="Retrieve information from a device or host")


@app.command("device")
def device_info(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target network device")],
) -> None:
    """Retrieve and display general information from a network device."""
    run_playbook("info_device", host, {})


@app.command("system")
def system_info(
    host: Annotated[str, typer.Argument(help="Inventory hostname of the target Linux host")],
    host_ip: Annotated[Optional[str], typer.Option("--host", help="Override the target IP or hostname (e.g. 172.20.20.21)")] = None,
) -> None:
    """Collect and display Linux system information (hostname, CPU, memory, disk, users, top processes)."""
    extra = {}
    if host_ip:
        extra["ansible_host"] = host_ip
    run_playbook("info_system", host, extra)
