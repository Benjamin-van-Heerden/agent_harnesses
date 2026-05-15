import typer

from src.state import logs


def run(filename: str) -> None:
    record = logs.get(filename)
    if record is None:
        typer.echo(f"Log not found: {filename}", err=True)
        raise typer.Exit(code=1)
    typer.echo(record.body.strip())
