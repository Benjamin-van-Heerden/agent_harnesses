import typer

from src.state import optional_docs


def run() -> None:
    try:
        statuses = optional_docs.list_statuses()
    except optional_docs.OptionalDocsError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    if not statuses:
        typer.echo("No optional docs are available.")
        return

    for status in statuses:
        typer.echo(f"{status.slug}: {status.status}")
