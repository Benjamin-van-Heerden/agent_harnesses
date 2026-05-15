from __future__ import annotations

import typer

from src.commands.log.utils.formatting import format_summary
from src.state import logs


def run(limit: int = 10, spec_slug: str | None = None, username: str | None = None) -> None:
    records = logs.list_all(limit=limit, spec_slug=spec_slug, username=username)
    if not records:
        typer.echo("No logs found.")
        return
    for record in records:
        typer.echo(format_summary(record))
