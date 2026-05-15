from __future__ import annotations

import typer

from src.commands.todo.utils.formatting import format_summary
from src.state import todos


def run(status: str | None = None) -> None:
    records = todos.list_all(status=status)
    if not records:
        typer.echo("No todos found.")
        return
    for record in records:
        typer.echo(format_summary(record))
