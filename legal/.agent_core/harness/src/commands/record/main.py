import typer


app = typer.Typer(help="Manage matter chronology records")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Record commands are scaffolded. Native chronology behavior has not been ported yet.")
