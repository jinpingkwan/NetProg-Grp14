import typer

from cli.commands import configure, discover, info

app = typer.Typer(
    no_args_is_help=True,
    help="NetAuto — network & Linux infrastructure automation toolkit",
)

app.add_typer(configure.app, name="configure")
app.add_typer(info.app, name="info")
app.add_typer(discover.app, name="discover")

if __name__ == "__main__":
    app()
