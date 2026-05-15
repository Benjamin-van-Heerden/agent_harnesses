import typer

from src.commands.merge import into, pr


app = typer.Typer(help="Merge pull requests and promote protected branches")


@app.callback(invoke_without_command=True)
def run(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


app.command("pr")(pr.run)
app.command("into")(into.run)
