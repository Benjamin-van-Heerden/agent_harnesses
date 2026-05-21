import typer


app = typer.Typer(help="Manage legal obligations")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Obligation commands are scaffolded. Native obligation behavior has not been ported yet.")
