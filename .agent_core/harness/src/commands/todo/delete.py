from __future__ import annotations

import typer

from src.commands.todo.utils.resolve import resolve_or_exit
from src.state import todos


def run(identifier: str) -> None:
    slug = resolve_or_exit(identifier)
    todos.delete(slug)
    typer.echo(f"Deleted: {slug}")
