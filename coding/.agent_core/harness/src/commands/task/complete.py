from __future__ import annotations

import typer
from typing_extensions import Annotated

from src.state import tasks


def run(
    spec_slug: str,
    slug: str,
    notes: Annotated[str, typer.Argument()] = "",
) -> None:
    tasks.complete(spec_slug, slug, notes)
    typer.echo(f"Completed: {slug}")
