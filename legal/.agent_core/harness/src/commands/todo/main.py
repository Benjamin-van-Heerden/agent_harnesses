from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.todos import claim_todo, create_todo, list_all_todos, list_claimed_matter_todos, list_matter_todos
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage global and matter todos")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a todo subcommand.")


@app.command("list")
def list_command(matter_ref: Annotated[str, typer.Argument()] = "") -> None:
    todos = (
        list_matter_todos(matter_ref) + list_claimed_matter_todos(matter_ref)
        if matter_ref
        else list_all_todos()
    )
    typer.echo("slug\tpriority\ttitle\tstatus\tscope\tpath")
    for todo in todos:
        scope = "global" if todo.matter == "null" else todo.matter
        typer.echo(
            f"{todo.slug}\t{todo.priority}\t{todo.title}\t{todo.status}\t{scope}\t"
            f"{todo.path.relative_to(PROJECT_PATHS.project_root)}"
        )
    if not todos:
        typer.echo("(no open todos)")


@app.command("new")
def new_command(
    slug: Annotated[str, typer.Argument()],
    title: Annotated[str, typer.Argument()],
    priority: Annotated[str, typer.Argument()] = "normal",
    matter_ref: Annotated[str, typer.Argument()] = "",
) -> None:
    try:
        todo_file = create_todo(slug, title, priority, matter_ref)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    scope = "matter" if matter_ref else "global"
    typer.echo(f"Created {scope} todo: {slug}")
    typer.echo(f"Todo: {todo_file.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must complete the todo description if the title is not enough context for the next session.")


@app.command("claim")
def claim_command(
    slug: Annotated[str, typer.Argument()],
    matter_ref: Annotated[str, typer.Argument()] = "",
) -> None:
    try:
        todo_file = claim_todo(slug, matter_ref)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Claimed todo: {slug}")
    typer.echo(f"Todo: {todo_file.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must do the claimed work or tell the lawyer what remains blocked.")
