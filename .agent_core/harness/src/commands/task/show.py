from __future__ import annotations

import typer

from src.commands.task.utils.formatting import format_detail
from src.state import tasks


def run(spec_slug: str, slug: str) -> None:
    record = tasks.get(spec_slug, slug)
    if record is None:
        typer.echo(f"Task not found: {slug}", err=True)
        raise typer.Exit(code=1)
    typer.echo(format_detail(record))
