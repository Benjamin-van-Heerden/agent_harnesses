import typer
from typing import cast

from src.utils.listing import short_datetime, table_lines
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
    parsed_status = _parse_status(status)
    records = todos.list_all(status=parsed_status)
    if not records:
        status_text = f" {parsed_status}" if parsed_status else ""
        typer.echo(f"No{status_text} todos found.")
        return

    open_count = sum(1 for record in todos.list_all() if record.status == "open")
    typer.echo("TODOS")
    typer.echo(f"Open: {open_count}")
    if parsed_status is not None:
        typer.echo(f"Filter: {parsed_status}")
    typer.echo("")

    columns = [
        ("Status", 10),
        ("Slug", 34),
        ("Title", 42),
        ("Issue", 42),
        ("Claimed By", 24),
        ("Date", 16),
    ]
    rows = [
        [
            record.status,
            record.slug,
            record.title,
            record.issue_url
            or (str(record.issue_id) if record.issue_id is not None else "N/A"),
            record.claimed_by or "N/A",
            short_datetime(record.claimed_at or record.created_at),
        ]
        for record in records
    ]
    for line in table_lines(columns, rows):
        typer.echo(line)

    typer.echo("")
    typer.echo(f"Total: {len(records)} todo(s)")
    if open_count:
        typer.echo("Open todos must be claimed before work starts.")
    typer.echo('Claim: python -B .agent_core/harness/main.py todo claim "<title or slug>" <user>')
