import typer
from typing_extensions import Annotated

from src.commands.task.utils.active import resolve_spec_slug
from src.state import tasks


def run(
    slug: str,
    notes: Annotated[str, typer.Argument()] = "",
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
) -> None:
    tasks.complete(resolve_spec_slug(spec_slug), slug, notes)
    typer.echo(f"Completed: {slug}")
