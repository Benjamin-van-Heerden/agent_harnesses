from __future__ import annotations

import typer

from src.commands.task.utils.formatting import format_summary
from src.state import tasks


def run(spec_slug: str, status: str | None = None) -> None:
    records = tasks.list_all(spec_slug, status=status)
    if not records:
        typer.echo("No tasks found.")
        return
    for record in records:
        typer.echo(format_summary(record))
