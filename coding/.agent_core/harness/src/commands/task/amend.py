import typer
from typing_extensions import Annotated

from src.commands.task.utils.active import resolve_spec_slug
from src.state import tasks


def run(
    slug: str,
    notes: str,
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
) -> None:
    tasks.amend(resolve_spec_slug(spec_slug), slug, notes)
    typer.echo(f"Amended: {slug}")
