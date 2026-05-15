from __future__ import annotations

import typer

from src.commands.spec.utils.formatting import format_summary
from src.state import specs


def run(status: str | None = None) -> None:
    records = specs.list_all(status=status)
    if not records:
        typer.echo("No specs found.")
        return
    for record in records:
        typer.echo(format_summary(record))
