from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.todos import list_matter_todos, list_practice_todos


app = typer.Typer(help="Manage practice and matter todos")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a todo subcommand.")


@app.command("list")
def list_command(matter_ref: Annotated[str, typer.Argument()] = "") -> None:
    todos = list_matter_todos(matter_ref) if matter_ref else list_practice_todos()
    typer.echo("slug\tpriority\ttitle\tpath")
    for todo in todos:
        typer.echo(f"{todo.slug}\t{todo.priority}\t{todo.title}\t{todo.path.relative_to(PROJECT_PATHS.project_root)}")
    if not todos:
        typer.echo("(no open todos)")
