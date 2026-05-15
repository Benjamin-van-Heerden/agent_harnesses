from __future__ import annotations

import typer

from src.commands.memory.utils.formatting import format_detail
from src.commands.memory.utils.resolve import resolve_or_exit
from src.state import memories


def run(identifier: str) -> None:
    slug = resolve_or_exit(identifier)
    record = memories.get(slug)
    if record is None:
        typer.echo(f"Memory not found: {identifier}", err=True)
        raise typer.Exit(code=1)
    typer.echo(format_detail(record))
