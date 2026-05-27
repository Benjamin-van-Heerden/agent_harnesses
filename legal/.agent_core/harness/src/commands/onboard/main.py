from collections.abc import Sequence
from pathlib import Path

import typer

from src.config.paths import PROJECT_PATHS
from src.state.client_index import refresh_client_matter_index
from src.state.clients import list_clients
from src.state.logs import cleanup_empty_work_logs, create_work_log, recent_work_logs
from src.state.matters import list_open_matters
from src.state.memories import list_memories
from src.state.obligations import upcoming_obligations
from src.state.todos import list_all_todos
from src.utils import auto_update
from src.utils.git import post_command_snapshot


app = typer.Typer(help="Build legal practice context for the agent")
PLACEHOLDER = "PLACEHOLDER - NOT YET FILLED IN"
FILE_WIDTH = 50


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


def _read_text(path: Path) -> str:
    try:
        return path.read_text().strip()
    except UnicodeDecodeError:
        return "[Skipped binary or non-text file]"
    except OSError as error:
        return f"[Could not read file: {error}]"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def _section(title: str) -> None:
    typer.echo("")
    typer.echo(title)
    typer.echo("-" * len(title))


def _file(title: str) -> None:
    typer.echo("#" * FILE_WIDTH)
    typer.echo(f"# {title}")
    typer.echo("#" * FILE_WIDTH)
    typer.echo("")


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    typer.echo("| " + " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers)) + " |")
    typer.echo("| " + " | ".join("-" * width for width in widths) + " |")
    for row in rows:
        typer.echo("| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |")


def _todo_scope(matter: str) -> str:
    return "Global" if matter == "null" else matter


def _onboard_docs() -> list[Path]:
    candidates = [
        PROJECT_PATHS.legal_context,
    ]
    return [path for path in candidates if path.is_file() and _read_text(path)]


@app.callback(invoke_without_command=True)
def run() -> None:
    """Build the initial legal context for the agent."""
    try:
        update_result = auto_update.maybe_update()
    except auto_update.AutoUpdateError as error:
        typer.echo("Onboard stopped before building legal context.", err=True)
        typer.echo(f"Harness auto-update failed: {error}", err=True)
        typer.echo("", err=True)
        typer.echo(
            "Resolve the harness update failure, or set AGENT_CORE_SKIP_AUTO_UPDATE=1 and rerun onboard.",
            err=True,
        )
        raise typer.Exit(code=1) from error
    if update_result.skipped_reason:
        typer.echo(f"Harness auto-update skipped: {update_result.skipped_reason}")
    if update_result.reexec_required:
        typer.echo("Harness updated. Restarting onboard with the refreshed harness.")
        auto_update.reexec_current_command()

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
    client_index = refresh_client_matter_index()
    obligations = upcoming_obligations(14)
    memories = list_memories()
    removed_logs = cleanup_empty_work_logs()
    logs = recent_work_logs(3)
    session_log = create_work_log()
    todos = list_all_todos()
    typst_files = _typst_files()
    high_priority = [matter for matter in open_matters if matter.priority in ("high", "urgent")]
    onboard_docs = _onboard_docs()
    post_command_snapshot(PROJECT_PATHS.project_root)

    typer.echo("Legal onboard context")
    typer.echo("=====================")

    _section("Workspace")
    _table(
        ("Item", "Value"),
        [
            ("Project root", str(PROJECT_PATHS.project_root)),
            ("Lawyer profile", "present" if profile_ready else "missing"),
            ("Session work log", str(session_log.relative_to(PROJECT_PATHS.project_root))),
        ],
    )

    if placeholder_files:
        _section("Setup warnings")
        for path in placeholder_files:
            typer.echo(f"- Placeholder remains: {path.relative_to(PROJECT_PATHS.project_root)}")

    if onboard_docs:
        _section("Required docs")
        for path in onboard_docs:
            _file(_relative(path))
            typer.echo(_read_text(path))
            typer.echo("")

    _section("Practice summary")
    _table(
        ("Metric", "Count"),
        [
            ("Clients", str(len(clients))),
            ("Open matters", str(len(open_matters))),
            ("Upcoming obligations within 14 days", str(len(obligations))),
            ("High-priority matters", str(len(high_priority))),
            ("Practice memories", str(len(memories))),
            ("Recent work logs", str(len(logs))),
            ("Typst building blocks", str(len(typst_files))),
        ],
    )

    if removed_logs:
        _section("Work-log cleanup")
        typer.echo(f"Removed empty work logs: {len(removed_logs)}")

    if client_index:
        _section("Client matter index")
        rows = []
        for entry in client_index:
            if entry.matters:
                matters = "; ".join(
                    f"{summary.matter.matter_dir.name} ({summary.matter.last_touched_at or 'not touched'})"
                    for summary in entry.matters
                )
            else:
                matters = "(no matters)"
            rows.append((entry.client.display_name, matters))
        _table(("Client", "Recent matters"), rows)

    if obligations:
        _section("Upcoming obligations")
        rows = []
        for due_date, matter_dir, obligation in obligations:
            rows.append(
                (
                    due_date,
                    obligation.kind,
                    obligation.description,
                    str(matter_dir.relative_to(PROJECT_PATHS.project_root)),
                )
            )
        _table(("Due", "Kind", "Description", "Matter"), rows)

    if high_priority:
        _section("High-priority matters")
        rows = []
        for matter in high_priority:
            rows.append(
                (
                    matter.priority,
                    matter.client,
                    matter.matter_type,
                    str(matter.matter_dir.relative_to(PROJECT_PATHS.project_root)),
                )
            )
        _table(("Priority", "Client", "Type", "Matter"), rows)

    if todos:
        _section("Todos")
        grouped: dict[str, list[tuple[str, str, str]]] = {}
        for todo in todos:
            grouped.setdefault(_todo_scope(todo.matter), []).append(
                (todo.status, todo.priority, todo.title or todo.slug)
            )
        for scope in sorted(grouped, key=lambda value: (value != "Global", value)):
            typer.echo("")
            typer.echo(f"{scope}")
            _table(("Status", "Priority", "Todo"), grouped[scope])

    _section("Agent instructions")
    typer.echo("Your next response must brief the lawyer in plain language.")
    if todos:
        typer.echo("Present surfaced todos grouped by global and matter scope.")
    typer.echo("Do not mention command names, slugs, paths, or git details unless asked.")
    read_targets = "profile, legal context, matter files, memories, and logs"
    if todos:
        read_targets += ", plus surfaced todos"
    typer.echo(f"You must read the relevant {read_targets} before doing substantive legal work.")
    typer.echo("Keep the session work log updated as work happens. If no meaningful work happens, the next onboard will remove the untouched empty log.")
