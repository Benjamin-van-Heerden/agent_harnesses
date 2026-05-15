from __future__ import annotations

import typer

from src.state import specs


def run(slug: str) -> None:
    path = specs.update_status(slug, "abandoned")
    typer.echo(f"Abandoned: {path}")
