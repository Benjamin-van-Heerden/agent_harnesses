import typer
from typing import cast

from src.commands.todo.utils.formatting import format_summary
from src.models.frontmatter import TodoStatus
from src.state import todos

TODO_STATUSES: tuple[TodoStatus, ...] = ("open", "claimed")


def _parse_status(status: str | None) -> TodoStatus | None:
    if status is None:
        return None
    if status in TODO_STATUSES:
        return cast(TodoStatus, status)
    allowed = ", ".join(TODO_STATUSES)
    typer.echo(f"Invalid todo status '{status}'. Expected one of: {allowed}", err=True)
    raise typer.Exit(code=1)


def run(status: str | None = None) -> None:
    records = todos.list_all(status=_parse_status(status))
    if not records:
        typer.echo("No todos found.")
        return
    for record in records:
        typer.echo(format_summary(record))
