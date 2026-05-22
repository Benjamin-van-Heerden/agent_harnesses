import typer

from src.utils.listing import short_datetime, table_lines
from src.state import memories
from src.state.models import Memory


def _preview(record: Memory, max_chars: int = 70) -> str:
    body = " ".join(record.body.split())
    if len(body) <= max_chars:
        return body or "N/A"
    return f"{body[: max_chars - 3]}..."


def run() -> None:
    records = memories.list_all()
    if not records:
        typer.echo("No memories found.")
        return

    typer.echo("PROJECT MEMORIES")
    typer.echo("")
    columns = [
        ("Title", 34),
        ("Slug", 34),
        ("Updated", 16),
        ("Preview", 70),
    ]
    rows = [
        [
            record.title,
            record.slug,
            short_datetime(record.updated_at),
            _preview(record),
        ]
        for record in records
    ]
    for line in table_lines(columns, rows):
        typer.echo(line)

    typer.echo("")
    typer.echo(f"Total: {len(records)} memory/memories")
    typer.echo("View details: python -B .agent_core/harness/main.py memory show <slug>")
