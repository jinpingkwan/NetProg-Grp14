from typing import Annotated

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
) -> None:
    """Collect and display Linux system information (hostname, CPU, memory, disk, users, top processes)."""
    run_playbook("info_system", host, {})
