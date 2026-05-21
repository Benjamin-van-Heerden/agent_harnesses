import typer


app = typer.Typer(help="Manage practice memories")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Memory commands are scaffolded. Native memory behavior has not been ported yet.")
