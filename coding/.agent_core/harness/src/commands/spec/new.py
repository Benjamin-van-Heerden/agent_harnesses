from __future__ import annotations

import typer

from src.commands.spec.models.result import SpecCommandResult
from src.state import specs


def run(title: str, body: str | None = None) -> None:
    path = specs.create(title, body=body or specs.DEFAULT_BODY)
    result = SpecCommandResult(slug=path.parent.name, path=path)
    typer.echo(f"Created: {result.path}")
