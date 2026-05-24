import typer

from src.config.branches import get_branch_names
from src.utils import git, worktrees


def require_dev_main_repo(action: str) -> str:
    branches = get_branch_names()
    current = git.current_branch()
    if worktrees.is_worktree():
        typer.echo(f"Error: Cannot {action} from a worktree.", err=True)
        typer.echo(f"Run this command from the main repository on the {branches.dev} branch.", err=True)
        raise typer.Exit(code=1)
    if current != branches.dev:
        typer.echo(
            f"Error: Must be on '{branches.dev}' to {action}. Currently on '{current or 'detached HEAD'}'.",
            err=True,
        )
        typer.echo(f"Run: git switch {branches.dev}", err=True)
        raise typer.Exit(code=1)
    return branches.dev
