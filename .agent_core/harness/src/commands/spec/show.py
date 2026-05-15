import typer

from src.commands.spec.utils.formatting import format_detail
from src.state import specs


def run(slug: str) -> None:
    record = specs.get(slug)
    if record is None:
        typer.echo(f"Spec not found: {slug}", err=True)
        raise typer.Exit(code=1)
    typer.echo(format_detail(record))
