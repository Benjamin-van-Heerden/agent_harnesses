from __future__ import annotations

import typer

from src.state import tasks


def run(spec_slug: str, slug: str, notes: str) -> None:
    tasks.amend(spec_slug, slug, notes)
    typer.echo(f"Amended: {slug}")
