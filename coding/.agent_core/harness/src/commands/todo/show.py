import typer

from src.commands.todo.utils.formatting import format_detail
from src.commands.todo.utils.resolve import resolve_or_exit
from src.state import todos


def run(identifier: str) -> None:
    slug = resolve_or_exit(identifier)
    record = todos.get(slug)
    if record is None:
        typer.echo(f"Todo not found: {identifier}", err=True)
        raise typer.Exit(code=1)
    typer.echo(format_detail(record))
