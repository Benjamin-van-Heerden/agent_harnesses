from __future__ import annotations

import typer

from src.state import logs


def run(spec_slug: str | None = None) -> None:
    path = logs.create(spec_slug=spec_slug)
    typer.echo(f"Created: {path}")
