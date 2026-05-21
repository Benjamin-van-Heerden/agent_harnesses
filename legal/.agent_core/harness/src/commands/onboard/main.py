from pathlib import Path

import typer

from src.config.paths import PROJECT_PATHS
from src.state.clients import list_clients
from src.state.deadlines import upcoming_deadlines
from src.state.logs import recent_work_logs
from src.state.matters import list_open_matters
from src.state.memories import list_memories
from src.state.todos import list_practice_todos


app = typer.Typer(help="Build legal practice context for the agent")
PLACEHOLDER = "PLACEHOLDER — NOT YET FILLED IN"


def _count_files(path: Path, pattern: str = "*.md") -> int:
    if not path.is_dir():
        return 0
    return sum(1 for candidate in path.rglob(pattern) if candidate.is_file())


def _has_placeholder(path: Path) -> bool:
    return path.is_file() and PLACEHOLDER in path.read_text(errors="ignore")


def _typst_files() -> list[Path]:
    if not PROJECT_PATHS.src_root.is_dir():
        return []
    return sorted(path for path in PROJECT_PATHS.src_root.rglob("*.typ") if path.is_file())


@app.callback(invoke_without_command=True)
def run() -> None:
    """Build the initial legal context for the agent."""
    profile_ready = PROJECT_PATHS.lawyer_profile.is_file()
    placeholder_files = [
        path
        for path in (
            PROJECT_PATHS.lawyer_profile,
            PROJECT_PATHS.legal_context,
        )
        if _has_placeholder(path)
    ]
    clients = list_clients()
    open_matters = list_open_matters()
    deadlines = upcoming_deadlines(14)
    memories = list_memories()
    logs = recent_work_logs(3)
    todos = list_practice_todos()
    typst_files = _typst_files()

    typer.echo("Legal onboard context")
    typer.echo(f"Project root: {PROJECT_PATHS.project_root}")
    typer.echo(f"Lawyer profile: {'present' if profile_ready else 'missing'}")
    if placeholder_files:
        typer.echo("Setup warnings:")
        for path in placeholder_files:
            typer.echo(f"- Placeholder remains: {path.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo(f"Clients: {len(clients)}")
    typer.echo(f"Open matters: {len(open_matters)}")
    typer.echo(f"Upcoming deadlines within 14 days: {len(deadlines)}")
    typer.echo(f"Practice memories: {len(memories)}")
    typer.echo(f"Recent work logs shown: {len(logs)}")
    typer.echo(f"Open practice todos: {len(todos)}")
    typer.echo(f"Typst building blocks: {len(typst_files)}")

    if deadlines:
        typer.echo("")
        typer.echo("Upcoming deadlines:")
        for due_date, matter_dir, deadline in deadlines:
            typer.echo(
                f"- {due_date}: {deadline.category} — {deadline.description} "
                f"({matter_dir.relative_to(PROJECT_PATHS.project_root)})"
            )

    high_priority = [matter for matter in open_matters if matter.priority in ("high", "urgent")]
    if high_priority:
        typer.echo("")
        typer.echo("High-priority matters:")
        for matter in high_priority:
            typer.echo(f"- {matter.priority}: {matter.matter_dir.relative_to(PROJECT_PATHS.project_root)}")

    if todos:
        typer.echo("")
        typer.echo("Open practice todos:")
        for todo in todos:
            typer.echo(f"- {todo.priority}: {todo.title or todo.slug}")

    typer.echo("")
    typer.echo("You must brief the lawyer in plain language. Do not mention command names, slugs, paths, or git details unless asked.")
    typer.echo("You must read the relevant profile, legal context, matter files, memories, logs, and todos before doing substantive legal work.")
