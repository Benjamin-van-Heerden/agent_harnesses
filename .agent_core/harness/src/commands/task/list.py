import typer
from typing import cast

from src.commands.task.utils.formatting import format_summary
from src.models.frontmatter import TaskStatus
from src.state import tasks

TASK_STATUSES: tuple[TaskStatus, ...] = ("todo", "completed")


def _parse_status(status: str | None) -> TaskStatus | None:
    if status is None:
        return None
    if status in TASK_STATUSES:
        return cast(TaskStatus, status)
    allowed = ", ".join(TASK_STATUSES)
    typer.echo(f"Invalid task status '{status}'. Expected one of: {allowed}", err=True)
    raise typer.Exit(code=1)


def run(spec_slug: str, status: str | None = None) -> None:
    records = tasks.list_all(spec_slug, status=_parse_status(status))
    if not records:
        typer.echo("No tasks found.")
        return
    for record in records:
        typer.echo(format_summary(record))
