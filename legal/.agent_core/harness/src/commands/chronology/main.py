from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.chronology import add_chronology_event, list_chronology
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage matter chronology")
add_app = typer.Typer(help="Add chronology events")
app.add_typer(add_app, name="add")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a chronology subcommand.")


def _add(kind: str, matter_ref: str, date: str, summary: str, body: str = "") -> None:
    try:
        event = add_chronology_event(matter_ref, date, kind, summary, body)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Added chronology event: {kind} — {summary}")
    typer.echo(f"Chronology: {event.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must update matter status or obligations if this event changes posture or future duties.")


@add_app.command("conversation")
def add_conversation(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    participants: Annotated[str, typer.Argument()],
    summary: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    _add("conversation", matter_ref, date, f"{participants} — {summary}", body)


@add_app.command("meeting")
def add_meeting(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    participants: Annotated[str, typer.Argument()],
    summary: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    _add("meeting", matter_ref, date, f"{participants} — {summary}", body)


@add_app.command("email")
def add_email(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    direction: Annotated[str, typer.Argument()],
    counterparty: Annotated[str, typer.Argument()],
    subject: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    if direction not in ("in", "out"):
        exit_on_error(ValueError("direction must be 'in' or 'out'"))
    _add("email", matter_ref, date, f"{direction}: {counterparty} — {subject}", body or "_TODO: body_")


@add_app.command("letter")
def add_letter(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    direction: Annotated[str, typer.Argument()],
    counterparty: Annotated[str, typer.Argument()],
    subject: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    if direction not in ("in", "out"):
        exit_on_error(ValueError("direction must be 'in' or 'out'"))
    _add("letter", matter_ref, date, f"{direction}: {counterparty} — {subject}", body)


@add_app.command("filing")
def add_filing(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    summary: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    _add("filing", matter_ref, date, summary, body)


@add_app.command("service")
def add_service(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    summary: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    _add("service", matter_ref, date, summary, body)


@add_app.command("note")
def add_note(
    matter_ref: Annotated[str, typer.Argument()],
    date: Annotated[str, typer.Argument()],
    summary: Annotated[str, typer.Argument()],
    body: Annotated[str, typer.Argument()] = "",
) -> None:
    _add("note", matter_ref, date, summary, body)


@app.command("list")
def list_command(matter_ref: Annotated[str, typer.Argument()]) -> None:
    try:
        entries = list_chronology(matter_ref)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo("date\tkind\tsummary")
    for entry in entries:
        typer.echo(f"{entry.date}\t{entry.kind}\t{entry.summary}")
    if not entries:
        typer.echo("(no chronology events)")
