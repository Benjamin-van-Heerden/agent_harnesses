#!/usr/bin/env python3
import deps

deps.require_dependencies()

import typer  # noqa: E402

from src.commands.cleanup.main import app as cleanup_app  # noqa: E402
from src.commands.log.main import app as log_app  # noqa: E402
from src.commands.memory.main import app as memory_app  # noqa: E402
from src.commands.merge.main import app as merge_app  # noqa: E402
from src.commands.onboard.main import app as onboard_app  # noqa: E402
from src.commands.report.main import app as report_app  # noqa: E402
from src.commands.spec.main import app as spec_app  # noqa: E402
from src.commands.sync.main import app as sync_app  # noqa: E402
from src.commands.task.main import app as task_app  # noqa: E402
from src.commands.todo.main import app as todo_app  # noqa: E402
from src.commands.worktree.main import app as worktree_app  # noqa: E402
from src.config.main import generate_default_config_toml, load_project_config  # noqa: E402
from src.config.paths import PROJECT_PATHS  # noqa: E402


app = typer.Typer(help="Project-local agent harness")
config_app = typer.Typer(help="Inspect project configuration")
app.add_typer(config_app, name="config")
app.add_typer(memory_app, name="memory")
app.add_typer(todo_app, name="todo")
app.add_typer(log_app, name="log")
app.add_typer(report_app, name="report")
app.add_typer(spec_app, name="spec")
app.add_typer(task_app, name="task")
app.add_typer(onboard_app, name="onboard")
app.add_typer(sync_app, name="sync")
app.add_typer(worktree_app, name="worktree")
app.add_typer(cleanup_app, name="cleanup")
app.add_typer(merge_app, name="merge")


@app.command()
def paths() -> None:
    """Print resolved project paths."""
    typer.echo(f"Project root: {PROJECT_PATHS.project_root}")
    typer.echo(f"State root: {PROJECT_PATHS.state_root}")
    typer.echo(f"Harness root: {PROJECT_PATHS.harness_root}")
    typer.echo(f"Config file: {PROJECT_PATHS.config_file}")


@config_app.command("show")
def show_config() -> None:
    """Validate and summarize the project config."""
    result = load_project_config(PROJECT_PATHS.config_file)
    if result.config is None:
        typer.echo(f"No valid config found at {PROJECT_PATHS.config_file_display}")
        raise typer.Exit(code=1)

    typer.echo(f"Project: {result.config.project.name}")
    typer.echo(f"Description: {result.config.project.description}")
    typer.echo(f"Dev branch: {result.config.branches.dev}")
    typer.echo(f"Main branch: {result.config.branches.main}")
    typer.echo(f"Test branch: {result.config.branches.test}")


@config_app.command("default")
def default_config() -> None:
    """Print a default config template."""
    typer.echo(generate_default_config_toml(PROJECT_PATHS.project_root.name))


if __name__ == "__main__":
    app()
