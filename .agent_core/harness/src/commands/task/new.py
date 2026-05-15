from __future__ import annotations

import typer
from typing_extensions import Annotated

from src.commands.task.models.result import TaskCommandResult
from src.state import tasks


def run(
    spec_slug: str,
    title: str,
    description: Annotated[str, typer.Argument()] = "",
) -> None:
    path = tasks.create(spec_slug, title, description)
    result = TaskCommandResult(slug=path.stem, path=path)
    typer.echo(f"Created: {result.path}")
