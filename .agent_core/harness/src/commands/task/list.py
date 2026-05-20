import typer
from typing import cast
from typing_extensions import Annotated

from src.commands.task.utils.active import resolve_spec_slug
from src.commands.utils.listing import short_datetime, table_lines
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


def run(
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
    status: str | None = None,
) -> None:
    resolved_spec_slug = resolve_spec_slug(spec_slug)
    parsed_status = _parse_status(status)
    all_records = tasks.list_all(resolved_spec_slug)
    records = tasks.list_all(resolved_spec_slug, status=parsed_status)
    if not records:
        status_text = f" {parsed_status}" if parsed_status else ""
        typer.echo(f"No{status_text} tasks found for spec '{resolved_spec_slug}'.")
        return

    completed = sum(1 for record in all_records if record.status == "completed")
    typer.echo(f"TASKS FOR SPEC: {resolved_spec_slug}")
    typer.echo(f"Completed: {completed}/{len(all_records)}")
    if parsed_status is not None:
        typer.echo(f"Filter: {parsed_status}")
    typer.echo("")

    columns = [
        ("Status", 12),
        ("Slug", 42),
        ("Title", 42),
        ("Updated", 16),
        ("Completed", 16),
    ]
    rows = [
        [
            record.status,
            record.slug,
            record.title,
            short_datetime(record.updated_at),
            short_datetime(record.completed_at),
        ]
        for record in records
    ]
    for line in table_lines(columns, rows):
        typer.echo(line)

    typer.echo("")
    typer.echo(f"Total: {len(records)} task(s)")
    typer.echo("View details: python -B .agent_core/harness/main.py task show <task_slug>")
