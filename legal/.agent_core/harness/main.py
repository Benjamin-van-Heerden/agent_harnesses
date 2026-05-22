#!/usr/bin/env python3
from pathlib import Path

import deps

deps.require_dependencies()

import typer  # noqa: E402

from src.commands.chronology.main import app as chronology_app  # noqa: E402
from src.commands.client.main import app as client_app  # noqa: E402
from src.commands.lint.main import app as lint_app  # noqa: E402
from src.commands.log.main import app as log_app  # noqa: E402
from src.commands.matter.main import app as matter_app  # noqa: E402
from src.commands.memory.main import app as memory_app  # noqa: E402
from src.commands.obligation.main import app as obligation_app  # noqa: E402
from src.commands.onboard.main import app as onboard_app  # noqa: E402
from src.commands.todo.main import app as todo_app  # noqa: E402
from src.config.main import load_config  # noqa: E402
from src.config.paths import PROJECT_PATHS, matter_chronology_dir, matter_obligations_dir, matter_todos_dir  # noqa: E402
from src.utils.git import post_command_snapshot  # noqa: E402


app = typer.Typer(help="Project-local legal agent harness")
config_app = typer.Typer(help="Inspect legal harness configuration")
app.add_typer(config_app, name="config")
app.add_typer(onboard_app, name="onboard")
app.add_typer(client_app, name="client")
app.add_typer(matter_app, name="matter")
app.add_typer(chronology_app, name="chronology")
app.add_typer(obligation_app, name="obligation")
app.add_typer(todo_app, name="todo")
app.add_typer(memory_app, name="memory")
app.add_typer(log_app, name="log")
app.add_typer(lint_app, name="lint")


@app.command()
def paths() -> None:
    """Print resolved project paths."""
    typer.echo(f"Project root: {PROJECT_PATHS.project_root}")
    typer.echo(f"State root: {PROJECT_PATHS.state_root}")
    typer.echo(f"Harness root: {PROJECT_PATHS.harness_root}")
    typer.echo(f"Practice root: {PROJECT_PATHS.practice_root}")
    typer.echo(f"Clients root: {PROJECT_PATHS.clients_root}")
    typer.echo(f"Docs root: {PROJECT_PATHS.docs_root}")
    typer.echo(f"Typst source root: {PROJECT_PATHS.src_root}")


@app.command("matter-paths")
def matter_paths(matter_path: Path) -> None:
    """Print derived state paths for a matter directory."""
    typer.echo(f"Matter root: {matter_path}")
    typer.echo(f"Chronology: {matter_chronology_dir(matter_path)}")
    typer.echo(f"Obligations: {matter_obligations_dir(matter_path)}")
    typer.echo(f"Todos: {matter_todos_dir(matter_path)}")


@config_app.command("show")
def show_config() -> None:
    """Validate and summarize legal harness configuration."""
    config = load_config(PROJECT_PATHS.config_file)
    typer.echo(f"Project: {config.project.name}")
    typer.echo(f"Harness: {config.harness.name}")
    typer.echo(f"Local git snapshots: {config.harness.local_git_snapshots}")
    typer.echo(f"Jurisdiction: {config.legal.jurisdiction or '(not set)'}")


if __name__ == "__main__":
    try:
        app()
    finally:
        post_command_snapshot(PROJECT_PATHS.project_root)
