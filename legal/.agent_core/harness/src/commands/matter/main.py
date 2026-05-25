from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.chronology import list_chronology
from src.state.matters import close_matter, create_matter, find_matters, list_open_matters, list_unparsed_files, resolve_matter, touch_matter
from src.state.obligations import list_obligations
from src.state.todos import list_claimed_matter_todos, list_matter_todos
from src.state.workflows import workflow_focus
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage legal matters")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a matter subcommand.")


@app.command("list")
def list_command() -> None:
    matters = list_open_matters()
    typer.echo("client\tmatter\ttype\tpriority\tnext_obligation\topen_todos\tpath")
    if not matters:
        typer.echo("(no open matters)")
        return
    for matter in matters:
        todos = list_matter_todos(str(matter.matter_dir.relative_to(PROJECT_PATHS.project_root)))
        rel = matter.matter_dir.relative_to(PROJECT_PATHS.project_root)
        typer.echo(
            f"{matter.client}\t{matter.matter_dir.name}\t{matter.matter_type}\t{matter.priority}\t"
            f"{matter.next_obligation}\t{len(todos)}\t{rel}"
        )


@app.command("new")
def new_command(
    client_slug: Annotated[str, typer.Argument()],
    matter_type: Annotated[str, typer.Argument()],
    matter_slug: Annotated[str, typer.Argument()],
    priority: Annotated[str, typer.Argument()] = "normal",
    billing: Annotated[str, typer.Argument()] = "hourly",
) -> None:
    try:
        matter_dir = create_matter(client_slug, matter_type, matter_slug, priority, billing)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Created matter: {matter_dir.name}")
    typer.echo(f"Matter: {matter_dir.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must review status, chronology, obligations, and todos before advising or drafting.")


@app.command("resolve")
def resolve_command(matter_ref: Annotated[str, typer.Argument()]) -> None:
    try:
        matter_dir = close_matter(matter_ref)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Resolved matter: {matter_dir.name}")
    typer.echo(f"Matter: {matter_dir.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must confirm the closure to the lawyer in plain language and note any unresolved practical follow-up.")


@app.command("find")
def find(pattern: str) -> None:
    matches = find_matters(pattern)
    for matter_dir in matches:
        typer.echo(matter_dir.relative_to(PROJECT_PATHS.project_root))
    if not matches:
        typer.echo("(no matching matters)")


@app.command("list-unparsed")
def list_unparsed(matter_ref: str) -> None:
    try:
        files = list_unparsed_files(matter_ref)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)
    if not files:
        typer.echo("(all raw files have a reference counterpart)")
        return
    for path in files:
        typer.echo(path.relative_to(PROJECT_PATHS.project_root))


@app.command("focus")
def focus(matter_ref: str) -> None:
    try:
        matter_dir = resolve_matter(matter_ref)
    except (FileNotFoundError, ValueError) as error:
        exit_on_error(error)
    touch_matter(matter_dir)
    status_file = matter_dir / "info" / "status.md"
    chronology_dir = matter_dir / "info" / "chronology"
    obligations_dir = matter_dir / "info" / "obligations"
    typst_files = sorted(path for path in matter_dir.glob("*.typ") if path.is_file())
    generated_pdf_files = sorted(path for path in matter_dir.glob("*.p.pdf") if path.is_file())
    other_pdf_files = sorted(
        path
        for path in matter_dir.glob("*.pdf")
        if path.is_file() and path.suffixes[-2:] != [".p", ".pdf"]
    )
    raw_files = sorted(path for path in (matter_dir / "raw").iterdir() if path.is_file()) if (matter_dir / "raw").is_dir() else []
    reference_files = sorted(path for path in (matter_dir / "reference").iterdir() if path.is_file()) if (matter_dir / "reference").is_dir() else []
    unparsed = list_unparsed_files(str(matter_dir.relative_to(PROJECT_PATHS.project_root)))
    matter_ref_path = str(matter_dir.relative_to(PROJECT_PATHS.project_root))
    todos = list_matter_todos(matter_ref_path) + list_claimed_matter_todos(matter_ref_path)
    chronology = list_chronology(str(matter_dir.relative_to(PROJECT_PATHS.project_root)))
    obligations = list_obligations(str(matter_dir.relative_to(PROJECT_PATHS.project_root)))
    workflow_state = workflow_focus(matter_dir)

    typer.echo(f"Focused matter: {matter_dir.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo(f"Status file: {'present' if status_file.is_file() else 'missing'}")
    typer.echo(f"Chronology directory: {'present' if chronology_dir.is_dir() else 'missing'}")
    typer.echo(f"Chronology events: {len(chronology)}")
    typer.echo(f"Obligations directory: {'present' if obligations_dir.is_dir() else 'missing'}")
    typer.echo(f"Open obligations: {len([obligation for obligation in obligations if obligation.status == 'open'])}")
    typer.echo(f"Matter todos: {len(todos)}")
    typer.echo(f"Typst drafts: {len(typst_files)}")
    typer.echo(f"Generated PDF outputs: {len(generated_pdf_files)}")
    typer.echo(f"Other PDFs: {len(other_pdf_files)}")
    typer.echo(f"Raw files: {len(raw_files)}")
    typer.echo(f"Reference files: {len(reference_files)}")
    typer.echo(f"Unparsed raw files: {len(unparsed)}")
    workflow_name = workflow_state.workflow.name if workflow_state is not None and workflow_state.workflow is not None else "(none)"
    if workflow_state is not None and workflow_state.error is not None:
        workflow_name = "(invalid)"
    typer.echo(f"Workflow: {workflow_name}")
    typer.echo("")
    typer.echo("Matter focus read set:")
    typer.echo(f"- Status: {status_file.relative_to(PROJECT_PATHS.project_root) if status_file.is_file() else 'missing'}")
    typer.echo(f"- Chronology: {min(len(chronology), 5)} recent event(s) shown below from {len(chronology)} total event(s)")
    typer.echo(f"- Open obligations: {len([obligation for obligation in obligations if obligation.status == 'open'])} shown below")
    typer.echo(f"- Drafts/outputs: {len(typst_files)} Typst source(s), {len(generated_pdf_files)} generated .p.pdf output(s), {len(other_pdf_files)} other PDF(s)")
    typer.echo(f"- Reference material: {len(reference_files)} reference file(s), {len(raw_files)} raw file(s), {len(unparsed)} unparsed raw file(s)")
    typer.echo(f"- Matter todos: {len(todos)} shown below")
    if workflow_state is not None:
        typer.echo(f"- Workflow next action: {workflow_state.next_action}")
        typer.echo(f"- Workflow blocked steps: {len(workflow_state.blocked_steps)}")
    if obligations:
        typer.echo("")
        typer.echo("Open obligations:")
        for obligation in obligations:
            if obligation.status == "open":
                typer.echo(f"- {obligation.due_date} - {obligation.kind} - {obligation.description}")
    if chronology:
        typer.echo("")
        typer.echo("Recent chronology:")
        for entry in chronology[-5:]:
            typer.echo(f"- {entry.date} - {entry.kind} - {entry.summary}")
    if todos:
        typer.echo("")
        typer.echo("Matter todos:")
        for todo in todos:
            typer.echo(f"- {todo.status} {todo.priority}: {todo.title or todo.slug}")
    if workflow_state is not None:
        typer.echo("")
        typer.echo("Workflow progress:")
        if workflow_state.error is not None:
            typer.echo(f"- Workflow error: {workflow_state.error}")
        elif workflow_state.workflow is not None:
            typer.echo(f"- Workflow: {workflow_state.workflow.name}")
        typer.echo(f"- Completed: {', '.join(workflow_state.progress.completed_steps) or '(none)'}")
        typer.echo(f"- Current: {', '.join(step.id for step in workflow_state.available_steps) or '(none)'}")
        typer.echo(f"- Blocked: {', '.join(step.id for step in workflow_state.blocked_steps) or '(none)'}")
        if workflow_state.missing_prerequisites:
            typer.echo("- Missing prerequisites:")
            for step_id, required in workflow_state.missing_prerequisites.items():
                typer.echo(f"  - {step_id}: {', '.join(required)}")
        typer.echo(f"- Next action: {workflow_state.next_action}")
        for step in workflow_state.available_steps:
            if step.todo:
                typer.echo(f"- Workflow todo: {step.todo}")
            if step.obligation:
                typer.echo(f"- Workflow obligation: {step.obligation}")
    if unparsed:
        typer.echo("")
        typer.echo("Unparsed raw files:")
        for path in unparsed:
            typer.echo(f"- {path.relative_to(PROJECT_PATHS.project_root)}")
    if typst_files or generated_pdf_files or other_pdf_files:
        typer.echo("")
        typer.echo("Drafts and outputs:")
        for path in typst_files:
            typer.echo(f"- Typst source: {path.relative_to(PROJECT_PATHS.project_root)}")
        for path in generated_pdf_files:
            typer.echo(f"- Generated PDF: {path.relative_to(PROJECT_PATHS.project_root)}")
        for path in other_pdf_files:
            typer.echo(f"- Other PDF: {path.relative_to(PROJECT_PATHS.project_root)}")
    if reference_files:
        typer.echo("")
        typer.echo("Reference files:")
        for path in reference_files:
            typer.echo(f"- {path.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("")
    typer.echo("Brief the lawyer in plain language. Do not mention file paths unless asked.")
