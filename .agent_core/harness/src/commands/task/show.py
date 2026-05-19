import typer
from typing_extensions import Annotated

from src.commands.task.utils.formatting import format_detail
from src.commands.task.utils.active import resolve_spec_slug
from src.state import tasks


def run(
    slug: str,
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
) -> None:
    record = tasks.get(resolve_spec_slug(spec_slug), slug)
    if record is None:
        typer.echo(f"Task not found: {slug}", err=True)
        raise typer.Exit(code=1)
    typer.echo(format_detail(record))
