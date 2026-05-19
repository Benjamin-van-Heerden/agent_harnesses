import typer

from src.config.branches import get_branch_names
from src.state import specs
from src.utils import git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.github import authenticated_username, repository, update_issue
from src.utils.markdown import slugify


def _require_synced_dev(branch: str) -> None:
    git.fetch()
    if not git.remote_branch_exists(branch):
        typer.echo(f"Error: Remote branch does not exist: origin/{branch}", err=True)
        typer.echo("Push or create the configured dev branch before assigning specs.", err=True)
        raise typer.Exit(code=1)

    local_ahead = git.local_ahead_of_remote(branch)
    remote_ahead = git.remote_ahead_of_local(branch)
    if local_ahead and remote_ahead:
        typer.echo(
            f"Error: Local `{branch}` and `origin/{branch}` have diverged.",
            err=True,
        )
        typer.echo("Resolve branch divergence before assigning specs.", err=True)
        raise typer.Exit(code=1)
    if local_ahead:
        typer.echo(
            f"Error: Local `{branch}` has commits that are not pushed to `origin/{branch}`.",
            err=True,
        )
        typer.echo("Push the checkpoint state before assigning specs.", err=True)
        raise typer.Exit(code=1)
    if remote_ahead:
        typer.echo(
            f"Error: `origin/{branch}` has commits that are not present locally.",
            err=True,
        )
        typer.echo("Sync the local dev branch before assigning specs.", err=True)
        raise typer.Exit(code=1)


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
        _require_synced_dev(branches.dev)
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
        checkpoint_message = f"prepare spec {slug} for assignment"
        checkpoint_created = False
        pushed_branch = ""

        if record.assigned_to != username:
            specs.update_assignment(slug, username)
        if record.branch != branch:
            specs.update_branch(slug, branch)

        git.add_all()
        if git.commit(checkpoint_message):
            checkpoint_created = True
        if checkpoint_created and current:
            git.push(current)
            pushed_branch = current

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
    if checkpoint_created:
        typer.echo("")
        typer.echo("Created and pushed assignment checkpoint:")
        typer.echo(f'  "{checkpoint_message}"')
        typer.echo(f"  branch: {pushed_branch}")
    else:
        typer.echo("")
        typer.echo("No assignment checkpoint commit was needed.")
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
