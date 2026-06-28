import typer

from cli.runner import run_playbook

app = typer.Typer(no_args_is_help=False, help="Discover and probe all hosts in the inventory")


@app.callback(invoke_without_command=True)
def discover(ctx: typer.Context) -> None:
    """Probe every host in the inventory and report reachable / unreachable status."""
    if ctx.invoked_subcommand is None:
        run_playbook("discover", "all", {})
