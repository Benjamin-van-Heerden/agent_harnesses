from datetime import date, datetime, timedelta

import typer

from src.state import logs


app = typer.Typer(help="Generate work reports")


def _week_bounds(reference: date) -> tuple[date, date]:
    start = reference - timedelta(days=reference.weekday())
    return start, start + timedelta(days=6)


@app.command("week")
def week(username: str | None = None) -> None:
    start, end = _week_bounds(date.today())
    records = [
        record
        for record in logs.list_all(limit=500, username=username)
        if start <= datetime.fromisoformat(record.created_at).date() <= end
    ]

    typer.echo(f"# Week Report: {start} to {end}")
    typer.echo("")

    if not records:
        typer.echo("No logs found for this week.")
        return

    for record in records:
        typer.echo(f"## {record.filename}")
        typer.echo("")
        typer.echo(record.body.strip())
        typer.echo("")
