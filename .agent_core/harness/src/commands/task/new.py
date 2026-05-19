import typer
from typing_extensions import Annotated

from src.commands.task.models.result import TaskCommandResult
from src.commands.task.utils.active import resolve_spec_slug
from src.state import tasks


def run(
    title: str,
    description: Annotated[str, typer.Argument()] = "",
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
) -> None:
    resolved_spec = resolve_spec_slug(spec_slug)
    path = tasks.create(resolved_spec, title, description)
    result = TaskCommandResult(slug=path.stem, path=path)
    typer.echo(f"Created: {result.path}")
