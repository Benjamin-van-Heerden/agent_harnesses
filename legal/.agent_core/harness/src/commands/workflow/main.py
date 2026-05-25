from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.workflows import create_workflow, link_matter_workflow, list_workflows, resolve_workflow
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage legal workflow templates")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a workflow subcommand.")


@app.command("new")
def new_command(name: Annotated[str, typer.Argument()]) -> None:
    try:
        path = create_workflow(name)
    except (FileExistsError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Created workflow: {path.stem}")
    typer.echo(f"Workflow: {path.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must edit and validate the workflow steps before relying on it for a matter.")


@app.command("list")
def list_command() -> None:
    try:
        workflows = list_workflows()
    except ValueError as error:
        exit_on_error(error)

    typer.echo("slug\tname\tsteps\tpath")
    if not workflows:
        typer.echo("(no workflows)")
        return
    for workflow in workflows:
        typer.echo(
            f"{workflow.slug}\t{workflow.name}\t{len(workflow.steps)}\t{workflow.path.relative_to(PROJECT_PATHS.project_root)}"
        )


@app.command("show")
def show_command(workflow_slug: Annotated[str, typer.Argument()]) -> None:
    try:
        workflow = resolve_workflow(workflow_slug)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Workflow: {workflow.name}")
    typer.echo(f"Slug: {workflow.slug}")
    typer.echo(f"Steps: {len(workflow.steps)}")
    typer.echo("id\tkind\trequires\tblocks\ttitle")
    for step in workflow.steps:
        typer.echo(
            f"{step.id}\t{step.kind}\t{','.join(step.requires) or '-'}\t{','.join(step.blocks) or '-'}\t{step.title}"
        )


@app.command("link")
def link_command(
    matter_ref: Annotated[str, typer.Argument()],
    workflow_slug: Annotated[str, typer.Argument()],
) -> None:
    try:
        progress_file = link_matter_workflow(matter_ref, workflow_slug)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Linked workflow: {workflow_slug}")
    typer.echo(f"Progress: {progress_file.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must run matter focus and brief the lawyer on the next workflow action.")
