from __future__ import annotations

import typer
from typing_extensions import Annotated

from src.state import todos


def run(title: str, description: Annotated[str, typer.Argument()] = "") -> None:
    path = todos.create(title, description)
    typer.echo(f"Created: {path}")
