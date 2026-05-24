import typer

from src.commands.utils.listing import short_datetime, table_lines
from src.state import logs


def run(
    limit: int = 10,
    spec_slug: str | None = None,
    username: str | None = None,
) -> None:
    records = logs.list_all(limit=limit, spec_slug=spec_slug, username=username)
    if not records:
        typer.echo("No logs found.")
        return

    typer.echo("WORK LOGS")
    typer.echo(f"Limit: {limit}")
    if spec_slug is not None:
        typer.echo(f"Spec filter: {spec_slug}")
    if username is not None:
        typer.echo(f"User filter: {username}")
    typer.echo("")

    columns = [
        ("Date", 16),
        ("User", 24),
        ("Spec", 42),
        ("Filename", 48),
    ]
    rows = [
        [
            short_datetime(record.created_at),
            record.username,
            record.spec_slug or "N/A",
            record.filename,
        ]
        for record in records
    ]
    for line in table_lines(columns, rows):
        typer.echo(line)

    typer.echo("")
    typer.echo(f"Total: {len(records)} log(s)")
    typer.echo("View details: python -B .agent_core/harness/main.py log show <filename>")
