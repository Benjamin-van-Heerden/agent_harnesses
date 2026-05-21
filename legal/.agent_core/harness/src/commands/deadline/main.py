from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.deadlines import upcoming_deadlines


app = typer.Typer(help="Manage legacy deadline-compatible obligation views")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a deadline subcommand.")


@app.command("upcoming")
def upcoming(days: Annotated[int, typer.Argument()] = 14) -> None:
    rows = upcoming_deadlines(days)
    typer.echo("date\tmatter\ttype\tdescription")
    for due_date, matter_dir, deadline in rows:
        typer.echo(
            f"{due_date}\t{matter_dir.relative_to(PROJECT_PATHS.project_root)}\t{deadline.category}\t{deadline.description}"
        )
    if not rows:
        typer.echo(f"(no deadlines within {days} days)")
