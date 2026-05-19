import typer
from typing_extensions import Annotated

from src.commands.task.utils.active import resolve_spec_slug
from src.state import tasks


def run(
    slug: str,
    title: str,
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
) -> None:
    path = tasks.rename(resolve_spec_slug(spec_slug), slug, title)
    typer.echo(f"Renamed: {path}")
