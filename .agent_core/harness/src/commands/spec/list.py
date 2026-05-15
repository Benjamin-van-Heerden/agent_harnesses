import typer
from typing import cast

from src.commands.spec.utils.formatting import format_summary
from src.models.frontmatter import SpecStatus
from src.state import specs

SPEC_STATUSES: tuple[SpecStatus, ...] = ("todo", "merge_ready", "completed", "abandoned")


def _parse_status(status: str | None) -> SpecStatus | None:
    if status is None:
        return None
    if status in SPEC_STATUSES:
        return cast(SpecStatus, status)
    allowed = ", ".join(SPEC_STATUSES)
    typer.echo(f"Invalid spec status '{status}'. Expected one of: {allowed}", err=True)
    raise typer.Exit(code=1)


def run(status: str | None = None) -> None:
    records = specs.list_all(status=_parse_status(status))
    if not records:
        typer.echo("No specs found.")
        return
    for record in records:
        typer.echo(format_summary(record))
