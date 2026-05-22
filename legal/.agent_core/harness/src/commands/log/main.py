from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.logs import create_work_log
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage practice work logs")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a log subcommand.")


@app.command("new")
def new_command(matter_ref: Annotated[str, typer.Argument()] = "") -> None:
    try:
        log_file = create_work_log(matter_ref)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Created work log: {log_file.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must replace every TODO in the work log with factual session details before ending the session.")
    typer.echo("After editing the log, tell the lawyer that the next session will pick up from it.")
