from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.memories import create_memory
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage practice memories")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a memory subcommand.")


@app.command("new")
def new_command(
    slug: Annotated[str, typer.Argument()],
    title: Annotated[str, typer.Argument()],
) -> None:
    try:
        memory_file = create_memory(slug, title)
    except (FileExistsError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Created memory: {slug}")
    typer.echo(f"Memory: {memory_file.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must replace the memory TODO with the durable practice note before relying on it in future sessions.")
