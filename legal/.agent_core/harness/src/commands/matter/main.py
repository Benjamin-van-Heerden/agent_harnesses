import typer

from src.config.paths import PROJECT_PATHS
from src.state.deadlines import read_deadlines
from src.state.matters import find_matters, list_open_matters, list_unparsed_files, resolve_matter
from src.state.todos import list_matter_todos


app = typer.Typer(help="Manage legal matters")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a matter subcommand.")


@app.command("list")
def list_command() -> None:
    matters = list_open_matters()
    typer.echo("client\tmatter\ttype\tpriority\tnext_deadline\topen_todos\tpath")
    if not matters:
        typer.echo("(no open matters)")
        return
    for matter in matters:
        todos = list_matter_todos(str(matter.matter_dir.relative_to(PROJECT_PATHS.project_root)))
        rel = matter.matter_dir.relative_to(PROJECT_PATHS.project_root)
        typer.echo(
            f"{matter.client}\t{matter.matter_dir.name}\t{matter.matter_type}\t{matter.priority}\t"
            f"{matter.next_deadline}\t{len(todos)}\t{rel}"
        )


@app.command("find")
def find(pattern: str) -> None:
    matches = find_matters(pattern)
    for matter_dir in matches:
        typer.echo(matter_dir.relative_to(PROJECT_PATHS.project_root))


@app.command("list-unparsed")
def list_unparsed(matter_ref: str) -> None:
    files = list_unparsed_files(matter_ref)
    if not files:
        typer.echo("(all raw files have a reference counterpart)")
        return
    for path in files:
        typer.echo(path.relative_to(PROJECT_PATHS.project_root))


@app.command("focus")
def focus(matter_ref: str) -> None:
    matter_dir = resolve_matter(matter_ref)
    status_file = matter_dir / "info" / "status.md"
    record_file = matter_dir / "info" / "record.md"
    deadlines_file = matter_dir / "info" / "deadlines.md"
    typst_files = sorted(path for path in matter_dir.glob("*.typ") if path.is_file())
    pdf_files = sorted(path for path in matter_dir.glob("*.pdf") if path.is_file())
    raw_files = sorted(path for path in (matter_dir / "raw").iterdir() if path.is_file()) if (matter_dir / "raw").is_dir() else []
    reference_files = sorted(path for path in (matter_dir / "reference").iterdir() if path.is_file()) if (matter_dir / "reference").is_dir() else []
    unparsed = list_unparsed_files(str(matter_dir.relative_to(PROJECT_PATHS.project_root)))
    todos = list_matter_todos(str(matter_dir.relative_to(PROJECT_PATHS.project_root)))
    deadlines = read_deadlines(deadlines_file)

    typer.echo(f"Focused matter: {matter_dir.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo(f"Status file: {'present' if status_file.is_file() else 'missing'}")
    typer.echo(f"Record file: {'present' if record_file.is_file() else 'missing'}")
    typer.echo(f"Deadlines: {len(deadlines)}")
    typer.echo(f"Open todos: {len(todos)}")
    typer.echo(f"Typst drafts: {len(typst_files)}")
    typer.echo(f"PDF outputs: {len(pdf_files)}")
    typer.echo(f"Raw files: {len(raw_files)}")
    typer.echo(f"Reference files: {len(reference_files)}")
    typer.echo(f"Unparsed raw files: {len(unparsed)}")
    if deadlines:
        typer.echo("")
        typer.echo("Deadlines:")
        for deadline in deadlines:
            typer.echo(f"- [{deadline.status}] {deadline.due_date} — {deadline.category} — {deadline.description}")
    if todos:
        typer.echo("")
        typer.echo("Open todos:")
        for todo in todos:
            typer.echo(f"- {todo.priority}: {todo.title or todo.slug}")
    if unparsed:
        typer.echo("")
        typer.echo("Unparsed raw files:")
        for path in unparsed:
            typer.echo(f"- {path.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("")
    typer.echo("You must read status, record, deadlines, relevant drafts, reference files, and listed todos before advising or drafting.")
    typer.echo("Brief the lawyer in plain language. Do not mention file paths unless asked.")
