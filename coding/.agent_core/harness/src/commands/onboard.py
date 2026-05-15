from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import typer

from src.config.main import load_project_config, summarize_validation_error
from src.config.paths import PROJECT_PATHS
from src.state import logs, memories, specs, tasks, todos


app = typer.Typer(help="Build local project context")


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return "[Skipped binary or non-text file]"
    except OSError as error:
        return f"[Could not read file: {error}]"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def _iter_docs() -> list[Path]:
    if not PROJECT_PATHS.docs_dir.exists():
        return []
    return sorted(
        (path for path in PROJECT_PATHS.docs_dir.rglob("*") if path.is_file()),
        key=lambda path: _relative(path).lower(),
    )


def _important_files_section(config) -> list[str]:
    lines: list[str] = []
    if not config.files:
        return lines

    lines.extend(["-" * 70, "IMPORTANT FILES", "-" * 70, ""])
    for item in config.files:
        path = PROJECT_PATHS.project_root / item.path
        lines.append(f"## {item.path}")
        if item.description:
            lines.append(f"*{item.description}*")
            lines.append("")
        lines.append(_read_text(path).strip())
        lines.append("")
    return lines


def _tree_dir(path: Path, max_entries: int = 300) -> str:
    if not path.exists():
        return f"{_relative(path)} (not found)"
    if not path.is_dir():
        return f"{_relative(path)} (not a directory)"

    entries: list[str] = []
    for index, child in enumerate(sorted(path.rglob("*"), key=lambda item: str(item).lower())):
        if index >= max_entries:
            entries.append("...")
            break
        if any(part in {".git", ".venv", "__pycache__", "node_modules"} for part in child.parts):
            continue
        entries.append(_relative(child) + ("/" if child.is_dir() else ""))
    return "\n".join(entries)


def _tree_sections(config) -> list[str]:
    lines: list[str] = []
    if not config.tree_dirs:
        return lines

    lines.extend(["-" * 70, "DIRECTORY TREES", "-" * 70, ""])
    for item in config.tree_dirs:
        path = PROJECT_PATHS.project_root / item.path
        lines.append(f"## {item.path}")
        if item.description:
            lines.append(f"*{item.description}*")
            lines.append("")
        lines.append("```text")
        lines.append(_tree_dir(path))
        lines.append("```")
        lines.append("")
    return lines


def _docs_section() -> list[str]:
    lines: list[str] = []
    docs = _iter_docs()
    if not docs:
        return lines

    lines.extend(["-" * 70, "PROJECT DOCS", "-" * 70, ""])
    for path in docs:
        lines.append(f"## {_relative(path)}")
        lines.append("")
        lines.append(_read_text(path).strip())
        lines.append("")
    return lines


def _state_section() -> list[str]:
    lines = ["-" * 70, "PROJECT STATE", "-" * 70, ""]

    records = specs.list_all()
    if records:
        lines.append("## Specs")
        for record in records:
            lines.append(f"- [{record.get('status', 'todo')}] {record.get('title', record['slug'])}")
            task_records = tasks.list_all(record["slug"])
            for task_record in task_records:
                lines.append(
                    f"  - [{task_record.get('status', 'todo')}] "
                    f"{task_record.get('title', task_record['slug'])}"
                )
        lines.append("")

    todo_records = todos.list_all(status="open")
    if todo_records:
        lines.append("## Open Todos")
        for record in todo_records:
            lines.append(f"- {record.get('title', record['slug'])}")
        lines.append("")

    memory_records = memories.list_all()
    if memory_records:
        lines.append("## Memories")
        for record in memory_records:
            lines.append(f"### {record.get('title', record['slug'])}")
            body = record.get("body", "").strip()
            if body:
                lines.append(body)
            lines.append("")

    log_records = logs.list_all(limit=5)
    if log_records:
        lines.append("## Recent Logs")
        for record in log_records:
            lines.append(f"- {record['filename']} ({record['created_at']})")
        lines.append("")

    if len(lines) == 4:
        lines.append("No specs, todos, memories, or logs found.")
        lines.append("")

    return lines


def _build_context() -> str:
    result = load_project_config(PROJECT_PATHS.config_file)
    if result.config is None:
        if result.validation_error is not None:
            summary = summarize_validation_error(result.validation_error)
            raise ValueError(f"Invalid {PROJECT_PATHS.config_file_display}:\n{summary}")
        raise ValueError(f"Missing or empty {PROJECT_PATHS.config_file_display}")

    config = result.config
    lines = [
        "=" * 70,
        "PROJECT CONTEXT",
        "=" * 70,
        "",
        f"Project: {config.project.name}",
        f"Description: {config.project.description}",
        f"Generated: {datetime.now().isoformat()}",
        "",
    ]

    lines.extend(_important_files_section(config))
    lines.extend(_tree_sections(config))
    lines.extend(_docs_section())
    lines.extend(_state_section())
    return "\n".join(lines).rstrip() + "\n"


def _write_output(content: str) -> Path:
    temp_dir = PROJECT_PATHS.state_root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now() - timedelta(hours=1)
    for path in temp_dir.glob("onboard_*.md"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                path.unlink()
        except OSError:
            pass

    output_path = temp_dir / f"onboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_path.write_text(content)
    return output_path


@app.callback(invoke_without_command=True)
def run(
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Print full context to stdout.",
    )
) -> None:
    try:
        content = _build_context()
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    if stdout or len(content) <= 14000:
        typer.echo(content)
        return

    output_path = _write_output(content)
    typer.echo(f"Onboard context written to: {_relative(output_path)}")
    typer.echo(f"Line count: {content.count(chr(10))}")
