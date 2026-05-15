from __future__ import annotations

import typer
from typing_extensions import Annotated

from src.state import memories


def run(title: str, content: Annotated[str, typer.Argument()] = "") -> None:
    path = memories.create(title, content)
    typer.echo(f"Created: {path}")
