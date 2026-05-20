import typer
from typing_extensions import Annotated

from src.config.branches import get_branch_names
from src.state import specs
from src.state.models import Spec
from src.state.user_mappings import require_mapped_user
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


def _require_assignment_context(slug: str, record: Spec) -> str:
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
        typer.echo(f"Run `python -B .agent_core/harness/main.py spec sync {slug}` first.")
        raise typer.Exit(code=1)
    return branches.dev


def _checkpoint_assignment(slug: str, current: str) -> tuple[bool, str, str]:
    checkpoint_message = f"prepare spec {slug} for assignment"
    checkpoint_created = False
    pushed_branch = ""

    git.add_all()
    if git.commit(checkpoint_message):
        checkpoint_created = True
        git.push(current)
        pushed_branch = current

    return checkpoint_created, checkpoint_message, pushed_branch


def _require_assignable(record: Spec, assignee: str) -> None:
    if record.assigned_to is not None and record.assigned_to != assignee:
        typer.echo(
            f"Error: Spec is already assigned to '{record.assigned_to}'.",
            err=True,
        )
        typer.echo(
            "Specs can only be reassigned by the current assignee or repo admin.",
            err=True,
        )
        raise typer.Exit(code=1)


def _print_checkpoint_status(
    checkpoint_created: bool,
    checkpoint_message: str,
    pushed_branch: str,
) -> None:
    if checkpoint_created:
        typer.echo("")
        typer.echo("Created and pushed assignment checkpoint:")
        typer.echo(f'  "{checkpoint_message}"')
        typer.echo(f"  branch: {pushed_branch}")
    else:
        typer.echo("")
        typer.echo("No assignment checkpoint commit was needed.")


def _assign_current_user(slug: str, record: Spec, username: str, dev_branch: str) -> None:
    branch = record.branch or f"{dev_branch}-{slugify(username)}-{slug}"
    checkpoint_created = False
    checkpoint_message = ""
    pushed_branch = ""

    if record.assigned_to != username:
        specs.update_assignment(slug, username)
    if record.branch != branch:
        specs.update_branch(slug, branch)

    checkpoint_created, checkpoint_message, pushed_branch = _checkpoint_assignment(slug, dev_branch)

    existing = [item for item in worktrees.list_all() if item.path == worktrees.path_for(slug)]
    if existing:
        typer.echo(f"Worktree already exists: {existing[0].path}")
        return

    path = worktrees.create(slug, branch)
    git.push(branch, cwd=path, set_upstream=True)

    repo = repository()
    if record.issue_id is not None:
        update_issue(repo, record.issue_id, assignees=[username])

    typer.echo("Assigned spec to authenticated GitHub user.")
    typer.echo(f"Assignee: {username}")
    typer.echo(f"Created worktree: {path}")
    typer.echo(f"Branch: {branch}")
    _print_checkpoint_status(checkpoint_created, checkpoint_message, pushed_branch)
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


def _assign_remote_user(slug: str, record: Spec, assignee: str, dev_branch: str) -> None:
    branch = record.branch or f"{dev_branch}-{slugify(assignee)}-{slug}"

    if record.assigned_to != assignee:
        specs.update_assignment(slug, assignee)
    if record.branch != branch:
        specs.update_branch(slug, branch)

    checkpoint_created, checkpoint_message, pushed_branch = _checkpoint_assignment(slug, dev_branch)
    git.push_ref("HEAD", branch)

    repo = repository()
    if record.issue_id is not None:
        update_issue(repo, record.issue_id, assignees=[assignee])

    typer.echo("Assigned spec to mapped GitHub user.")
    typer.echo(f"Assignee: {assignee}")
    typer.echo(f"Branch: {branch}")
    typer.echo("No local worktree was created for the current user.")
    _print_checkpoint_status(checkpoint_created, checkpoint_message, pushed_branch)
    typer.echo("")
    typer.echo("The assignee will receive the worktree when they run onboard.")


def run(
    slug: str,
    assignee: Annotated[
        str | None,
        typer.Option(
            "--assignee",
            help="Assign the spec to another mapped GitHub username without creating a local worktree.",
        ),
    ] = None,
) -> None:
    record = specs.get(slug)
    if record is None:
        typer.echo(f"Spec not found: {slug}", err=True)
        raise typer.Exit(code=1)

    try:
        dev_branch = _require_assignment_context(slug, record)
        username = authenticated_username()
        if assignee is None:
            _require_assignable(record, username)
            _assign_current_user(slug, record, username, dev_branch)
            return

        require_mapped_user(assignee)
        if assignee == username:
            typer.echo("Error: --assignee is for assigning specs to another mapped user.", err=True)
            typer.echo(f"Run `python -B .agent_core/harness/main.py spec assign {slug}` for current-user assignment.", err=True)
            raise typer.Exit(code=1)

        _require_assignable(record, assignee)
        _assign_remote_user(slug, record, assignee, dev_branch)
    except (GitError, GitHubError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
