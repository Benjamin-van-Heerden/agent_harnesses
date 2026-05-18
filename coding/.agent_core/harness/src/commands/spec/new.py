from pathlib import Path

import typer

from src.commands.spec.models.result import SpecCommandResult
from src.config.paths import PROJECT_PATHS
from src.state import specs


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def run(title: str, body: str | None = None) -> None:
    path = specs.create(title, body=body or specs.DEFAULT_BODY)
    result = SpecCommandResult(slug=path.parent.name, path=path)
    relative_path = _relative(result.path)

    typer.echo(f"Created spec: {relative_path}")
    typer.echo("")
    typer.echo("Spec created successfully.")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo(
        "1. Read the blank spec file so you understand what is expected for its body."
    )
    typer.echo(
        "2. Research the codebase, ask clarifying questions, and make sure you have enough information to write the spec body and tasks."
    )
    typer.echo(f"3. Edit the spec file: {relative_path}")
    typer.echo(
        f'4. Add tasks: `python -B .agent_core/harness/main.py task new "title" "detailed description with implementation notes" --spec {result.slug}`'
    )
    typer.echo(
        f"5. Run `python -B .agent_core/harness/main.py spec sync {result.slug}` to create the GitHub issue after the body and tasks are complete."
    )
    typer.echo(
        f"6. Run `python -B .agent_core/harness/main.py spec assign {result.slug}` to claim it and create a worktree."
    )
    typer.echo("")
    typer.echo("If this spec addresses any open todos, claim them.")
    typer.echo("")
    typer.echo("IMPORTANT: Worktree Workflow")
    typer.echo("")
    typer.echo("Create tasks before running `spec assign`.")
    typer.echo("After assignment, start a new agent session in the worktree.")
    typer.echo("")
    typer.echo("Remember:")
    typer.echo(
        "A new agent session will handle implementation work after assignment."
    )
    typer.echo(
        "That agent will only know the important files and decisions captured in the spec body and tasks."
    )
    typer.echo(
        "The spec body and tasks must be detailed enough for that agent to implement the work without additional context."
    )
