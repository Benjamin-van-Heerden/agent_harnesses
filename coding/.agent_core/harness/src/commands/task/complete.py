import typer
from typing_extensions import Annotated

from src.commands.task.utils.active import resolve_spec_slug
from src.state import tasks


def _permission_command(slug: str) -> str:
    return (
        f'python -B .agent_core/harness/main.py task complete {slug} '
        '"detailed notes about what was done" --user-gave-explicit-permission'
    )


def _print_permission_workflow(slug: str, title: str) -> None:
    typer.echo("")
    typer.echo("----------------------------------------------------------------------")
    typer.echo("AGENT INSTRUCTION: Task Completion Requires User Approval")
    typer.echo("----------------------------------------------------------------------")
    typer.echo("")
    typer.echo(f"Task: {title}")
    typer.echo(f"Slug: {slug}")
    typer.echo("")
    typer.echo("You must keep the user in the loop before marking this task complete.")
    typer.echo("")
    typer.echo("Required workflow:")
    typer.echo("1. Summarize the work completed for this task.")
    typer.echo('2. Ask the user: "Is this task complete and acceptable?"')
    typer.echo("3. Only after explicit user confirmation, re-run:")
    typer.echo(f"   {_permission_command(slug)}")
    typer.echo("")
    typer.echo("Never pass --user-gave-explicit-permission without explicit user approval.")
    typer.echo("----------------------------------------------------------------------")


def _print_completion_followup(spec_slug: str) -> None:
    records = tasks.list_all(spec_slug)
    pending = [record for record in records if record.status != "completed"]

    if not pending and records:
        typer.echo("")
        typer.echo("All tasks for this spec are complete.")
        typer.echo("")
        typer.echo("AGENT INSTRUCTION:")
        typer.echo("1. Summarize what was done for this task.")
        typer.echo("2. Ask the user if there is anything else to wrap up before completing the spec.")
        typer.echo("3. If the user is ready, create a work log and then complete the spec.")
        typer.echo("")
        typer.echo("Do not complete the spec without explicit user confirmation.")
        return

    if pending:
        typer.echo("")
        typer.echo(f"Remaining tasks ({len(pending)}):")
        for record in pending:
            typer.echo(f"  - {record.slug}: {record.title}")
        typer.echo("")
        typer.echo("You may continue with the next task.")
        typer.echo(
            "Before marking it complete, summarize the work and ask the user whether it is complete and acceptable."
        )
        typer.echo("Never assume permission carries over between tasks.")


def run(
    slug: str,
    notes: Annotated[str, typer.Argument()] = "",
    spec_slug: Annotated[
        str | None,
        typer.Option("--spec", help="Spec slug. Defaults to the active spec branch."),
    ] = None,
    user_gave_explicit_permission: Annotated[
        bool,
        typer.Option(
            "--user-gave-explicit-permission",
            help="User explicitly confirmed this task is complete.",
            hidden=True,
        ),
    ] = False,
) -> None:
    resolved_spec_slug = resolve_spec_slug(spec_slug)
    record = tasks.get(resolved_spec_slug, slug)
    if record is None:
        typer.echo(f"Task not found: {slug}", err=True)
        raise typer.Exit(code=1)

    if not user_gave_explicit_permission:
        _print_permission_workflow(slug, record.title)
        return

    tasks.complete(resolved_spec_slug, slug, notes)
    typer.echo(f"Completed: {record.title}")
    typer.echo(f"Slug: {slug}")
    _print_completion_followup(resolved_spec_slug)
