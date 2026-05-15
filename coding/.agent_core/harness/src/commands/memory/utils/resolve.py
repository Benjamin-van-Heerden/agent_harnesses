from __future__ import annotations

import typer

from src.state import memories


def resolve_or_exit(identifier: str) -> str:
    slug = memories.resolve(identifier)
    if slug is not None:
        return slug
    typer.echo(f"Memory not found: {identifier}", err=True)
    raise typer.Exit(code=1)
