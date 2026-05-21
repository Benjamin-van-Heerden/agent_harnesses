import typer


app = typer.Typer(help="Manage practice work logs")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Log commands are scaffolded. Native work log behavior has not been ported yet.")
