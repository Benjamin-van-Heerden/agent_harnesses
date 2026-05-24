import typer
from typing import cast

from src.utils.listing import short_date, short_datetime, table_lines
from src.models.frontmatter import SpecStatus
from src.state import specs
from src.state.models import Spec
from src.utils import git

SPEC_STATUSES: tuple[SpecStatus, ...] = ("todo", "merge_ready", "completed", "abandoned")


def _parse_status(status: str | None) -> SpecStatus | None:
    if status is None:
        return None
    if status in SPEC_STATUSES:
        return cast(SpecStatus, status)
    allowed = ", ".join(SPEC_STATUSES)
    typer.echo(f"Invalid spec status '{status}'. Expected one of: {allowed}", err=True)
    raise typer.Exit(code=1)


def _active_spec() -> Spec | None:
    branch = git.current_branch()
    if branch is None:
        return None
    for record in specs.list_all():
        if record.branch == branch and record.status in {"todo", "merge_ready"}:
            return record
    return None


def _records_for_status(status: SpecStatus | None) -> list[Spec]:
    if status is not None:
        records = specs.list_all(status=status)
    else:
        records = [
            record
            for record in specs.list_all()
            if record.status in {"todo", "merge_ready"}
        ]

    if status == "completed":
        records.sort(key=lambda item: item.completed_at or item.updated_at, reverse=True)
    return records


def run(status: str | None = None) -> None:
    parsed_status = _parse_status(status)
    records = _records_for_status(parsed_status)
    display_status = parsed_status.upper() if parsed_status else "TODO & MERGE_READY"
    if not records:
        typer.echo(f"No {display_status.lower()} specs found.")
        return

    active = _active_spec()
    if active is not None and parsed_status != "completed":
        typer.echo(f"Active spec: {active.slug} (branch: {active.branch or 'N/A'})")
        typer.echo("")

    typer.echo(f"{display_status} SPECS")
    typer.echo("")
    if parsed_status == "completed":
        columns = [
            ("Completed", 16),
            ("Title", 44),
            ("Slug", 42),
            ("PR", 36),
        ]
        rows = [
            [
                short_date(record.completed_at),
                record.title,
                record.slug,
                record.pr_url or "N/A",
            ]
            for record in records
        ]
    else:
        columns = [
            ("Active", 6),
            ("Status", 12),
            ("Slug", 38),
            ("Title", 34),
            ("Assignee", 24),
            ("Updated", 16),
        ]
        rows = [
            [
                "*" if active is not None and active.slug == record.slug else "",
                record.status,
                record.slug,
                record.title,
                record.assigned_to or "Unassigned",
                short_datetime(record.updated_at),
            ]
            for record in records
        ]
    for line in table_lines(columns, rows):
        typer.echo(line)

    typer.echo("")
    typer.echo(f"Total: {len(records)} spec(s)")
    if active is not None and parsed_status != "completed":
        typer.echo("* = currently active")
    typer.echo("View details: python -B .agent_core/harness/main.py spec show <slug>")
