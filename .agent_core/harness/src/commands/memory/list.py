from __future__ import annotations

import typer

from src.commands.memory.utils.formatting import format_summary
from src.state import memories


def run() -> None:
    records = memories.list_all()
    if not records:
        typer.echo("No memories found.")
        return
    for record in records:
        typer.echo(format_summary(record))
