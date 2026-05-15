from __future__ import annotations

import typer

from src.commands.memory.utils.resolve import resolve_or_exit
from src.state import memories


def run(identifier: str, content: str) -> None:
    slug = resolve_or_exit(identifier)
    memories.update(slug, content)
    typer.echo(f"Updated: {slug}")
