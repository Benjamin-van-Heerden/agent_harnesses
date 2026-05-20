from pathlib import Path

import typer

from src.commands.spec.models.result import SpecCommandResult
from src.config.branches import get_branch_names
from src.config.paths import PROJECT_PATHS
from src.state import specs
from src.utils import git, worktrees


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def run(title: str, body: str | None = None) -> None:
    branches = get_branch_names()
    current = git.current_branch()
    if worktrees.is_worktree():
        typer.echo("Error: Cannot create specs from a worktree.", err=True)
        typer.echo("Run this command from the main repository on the dev branch.", err=True)
        raise typer.Exit(code=1)
    if current != branches.dev:
        typer.echo(
            f"Error: Must be on '{branches.dev}' to create specs. Currently on '{current or 'detached HEAD'}'.",
            err=True,
        )
        typer.echo(f"Run: git checkout {branches.dev}", err=True)
        raise typer.Exit(code=1)

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
    typer.echo("6. Assign the spec only after explicit user approval:")
    typer.echo(
        f"   - Current user: `python -B .agent_core/harness/main.py spec assign {result.slug}` assigns it to the authenticated GitHub user and creates a local worktree."
    )
    typer.echo(
        f"   - Another user: `python -B .agent_core/harness/main.py spec assign {result.slug} --assignee <github_username>` assigns it to another mapped GitHub user, pushes the remote branch, and creates no local worktree for the current user."
    )
    typer.echo("")
    typer.echo("If this spec addresses any open todos, claim them.")
    typer.echo("")
    typer.echo(
        "DO NOT attempt to sync a spec without first filling in the body or creating at least one task."
    )
    typer.echo("")
    typer.echo("IMPORTANT: Worktree Workflow")
    typer.echo("")
    typer.echo("Create tasks before running `spec assign`.")
    typer.echo("Bare `spec assign` creates a local worktree for the authenticated GitHub user.")
    typer.echo("`spec assign --assignee <github_username>` creates remote assignment state only; the assignee receives the worktree on onboard.")
    typer.echo("After local assignment, start a new agent session in the worktree.")
    typer.echo("")
    typer.echo("Remember:")
    typer.echo("A new agent session will handle implementation work after assignment.")
    typer.echo(
        "That agent will only know the important files and decisions captured in the spec body and tasks."
    )
    typer.echo(
        "The spec body and tasks must be detailed enough for that agent to implement the work without additional context."
    )
