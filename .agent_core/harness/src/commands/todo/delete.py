import typer

from src.commands.todo.utils.context import require_todo_management_branch
from src.commands.todo.utils.resolve import resolve_or_exit
from src.state import todos


def run(identifier: str) -> None:
    require_todo_management_branch("delete todos")
    slug = resolve_or_exit(identifier)
    todos.delete(slug)
    typer.echo(f"Deleted: {slug}")
