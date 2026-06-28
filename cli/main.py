import typer

from cli.commands import configure, info

app = typer.Typer(
    no_args_is_help=True,
    help="NetAuto — network & Linux infrastructure automation toolkit",
)

app.add_typer(configure.app, name="configure")
app.add_typer(info.app, name="info")

if __name__ == "__main__":
    app()
