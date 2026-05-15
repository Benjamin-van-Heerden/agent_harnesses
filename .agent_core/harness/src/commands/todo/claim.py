from __future__ import annotations

import typer

from src.commands.todo.utils.resolve import resolve_or_exit
from src.state import todos


def run(identifier: str, claimed_by: str) -> None:
    slug = resolve_or_exit(identifier)
    path = todos.claim(slug, claimed_by)
    typer.echo(f"Claimed: {path}")
