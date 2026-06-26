import typer

from src.config.branches import get_branch_names
from src.state import specs
from src.utils import git, worktrees


def _is_active_spec_branch(branch: str | None) -> bool:
    if branch is None:
        return False
    return any(
        record.branch == branch and record.status in {"todo", "merge_ready"}
        for record in specs.list_all()
    )


def require_todo_management_branch(action: str) -> str:
    branches = get_branch_names()
    current = git.current_branch()

    if current == branches.dev or _is_active_spec_branch(current):
        return current

    if current in {branches.test, branches.main}:
        typer.echo(
            f"Error: Cannot {action} from protected branch '{current}'.",
            err=True,
        )
        typer.echo(
            f"Run this command from `{branches.dev}` or from an active spec branch that will merge back to `{branches.dev}`.",
            err=True,
        )
        raise typer.Exit(code=1)

    location = "worktree" if worktrees.is_worktree() else "branch"
    typer.echo(
        f"Error: Cannot {action} from this {location}: {current or 'detached HEAD'}.",
        err=True,
    )
    typer.echo(
        f"Run this command from `{branches.dev}` or from an active spec branch that will merge back to `{branches.dev}`.",
        err=True,
    )
    if current is not None:
        typer.echo(
            f"If `{current}` should be allowed, it must be recorded as an active spec branch.",
            err=True,
        )
    raise typer.Exit(code=1)
