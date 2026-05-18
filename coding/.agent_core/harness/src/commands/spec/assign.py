import typer

from src.config.branches import get_branch_names
from src.state import specs
from src.utils import git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.github import authenticated_username, repository, update_issue
from src.utils.markdown import slugify


def run(slug: str) -> None:
    record = specs.get(slug)
    if record is None:
        typer.echo(f"Spec not found: {slug}", err=True)
        raise typer.Exit(code=1)

    try:
        branches = get_branch_names()
        current = git.current_branch()
        if worktrees.is_worktree():
            typer.echo("Error: Cannot assign specs from a worktree.", err=True)
            typer.echo("Run this command from the main repository on the dev branch.", err=True)
            raise typer.Exit(code=1)
        if current != branches.dev:
            typer.echo(
                f"Error: Must be on '{branches.dev}' to assign specs. Currently on '{current or 'detached HEAD'}'.",
                err=True,
            )
            typer.echo(f"Run: git checkout {branches.dev}", err=True)
            raise typer.Exit(code=1)
        if record.issue_id is None:
            typer.echo(f"Error: Spec '{slug}' is not synced to GitHub.", err=True)
            typer.echo("")
            typer.echo(
                f"Run `python -B .agent_core/harness/main.py spec sync {slug}` first."
            )
            raise typer.Exit(code=1)

        username = authenticated_username()
        if record.assigned_to is not None and record.assigned_to != username:
            typer.echo(
                f"Error: Spec is already assigned to '{record.assigned_to}'.",
                err=True,
            )
            typer.echo(
                "Specs can only be reassigned by the current assignee or repo admin.",
                err=True,
            )
            raise typer.Exit(code=1)

        branch = record.branch or f"{branches.dev}-{slugify(username)}-{slug}"
        specs.update_assignment(slug, username)
        specs.update_branch(slug, branch)

        git.add_all()
        git.commit(f"prepare spec {slug} for assignment")
        if current:
            git.push(current)

        existing = [item for item in worktrees.list_all() if item.path == worktrees.path_for(slug)]
        if existing:
            typer.echo(f"Worktree already exists: {existing[0].path}")
            return

        path = worktrees.create(slug, branch)
        git.push(branch, cwd=path, set_upstream=True)

        repo = repository()
        update_issue(repo, record.issue_id, assignees=[username])

    except (GitError, GitHubError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Created worktree: {path}")
    typer.echo(f"Branch: {branch}")
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("WORKTREE READY - START NEW SESSION")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo("THIS SESSION MUST END HERE.")
    typer.echo("")
    typer.echo("To work on this spec, start a new agent session in the worktree:")
    typer.echo(f"  cd {path}")
    typer.echo("")
    typer.echo("WHY A NEW SESSION?")
    typer.echo("- The worktree is an isolated directory with its own branch.")
    typer.echo("- Implementation work from the main repo risks cross-branch pollution.")
    typer.echo("- A new session ensures clean separation of concerns.")
