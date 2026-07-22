from collections.abc import Callable

import typer

from src.state.optional_docs import OptionalDocsError


def run_or_exit(operation: Callable[[], list[str]]) -> None:
    try:
        messages = operation()
    except OptionalDocsError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    for message in messages:
        typer.echo(message)
