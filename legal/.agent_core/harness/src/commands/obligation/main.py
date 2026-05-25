from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.obligations import create_obligation, list_obligations
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage legal obligations")
add_app = typer.Typer(help="Add obligations")
app.add_typer(add_app, name="add")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use an obligation subcommand.")


def _add(kind: str, matter_ref: str, obligation_id: str, due_date: str, description: str) -> None:
    try:
        obligation = create_obligation(matter_ref, obligation_id, kind, due_date, description)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Added obligation: {kind} due {due_date} - {description}")
    typer.echo(f"Obligation: {obligation.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must consider whether this obligation needs a preparation todo or a status update.")


@add_app.command("deadline")
def add_deadline(
    matter_ref: Annotated[str, typer.Argument()],
    obligation_id: Annotated[str, typer.Argument()],
    due_date: Annotated[str, typer.Argument()],
    description: Annotated[str, typer.Argument()],
) -> None:
    _add("deadline", matter_ref, obligation_id, due_date, description)


@add_app.command("appearance")
def add_appearance(
    matter_ref: Annotated[str, typer.Argument()],
    obligation_id: Annotated[str, typer.Argument()],
    due_date: Annotated[str, typer.Argument()],
    description: Annotated[str, typer.Argument()],
) -> None:
    _add("court_appearance", matter_ref, obligation_id, due_date, description)


@add_app.command("follow-up")
def add_follow_up(
    matter_ref: Annotated[str, typer.Argument()],
    obligation_id: Annotated[str, typer.Argument()],
    due_date: Annotated[str, typer.Argument()],
    description: Annotated[str, typer.Argument()],
) -> None:
    _add("follow_up", matter_ref, obligation_id, due_date, description)


@add_app.command("preparation")
def add_preparation(
    matter_ref: Annotated[str, typer.Argument()],
    obligation_id: Annotated[str, typer.Argument()],
    due_date: Annotated[str, typer.Argument()],
    description: Annotated[str, typer.Argument()],
) -> None:
    _add("preparation", matter_ref, obligation_id, due_date, description)


@app.command("list")
def list_command(matter_ref: Annotated[str, typer.Argument()]) -> None:
    try:
        obligations = list_obligations(matter_ref)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo("due_date\tkind\tstatus\tdescription\tpath")
    for obligation in obligations:
        typer.echo(
            f"{obligation.due_date}\t{obligation.kind}\t{obligation.status}\t"
            f"{obligation.description}\t{obligation.path.relative_to(PROJECT_PATHS.project_root)}"
        )
    if not obligations:
        typer.echo("(no obligations)")
