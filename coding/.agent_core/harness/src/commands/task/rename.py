from __future__ import annotations

import typer

from src.state import tasks


def run(spec_slug: str, slug: str, title: str) -> None:
    path = tasks.rename(spec_slug, slug, title)
    typer.echo(f"Renamed: {path}")
