from typing import cast

import typer
from github.GithubException import GithubException
from github.Issue import Issue
from github.Repository import Repository

from src.config.branches import get_branch_names
from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import SpecStatus, TodoStatus, create_spec_frontmatter, create_todo_frontmatter
from src.state import specs, todos
from src.state.user_mappings import ensure_current_user_mapping, require_mapped_user
from src.utils import git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.github import (
    SPEC_LABEL,
    TODO_LABEL,
    authenticated_username,
    create_issue,
    delete_remote_branch,
    ensure_labels,
    issue_labels,
    list_issues,
    parse_pull_number,
    repository,
    status_from_labels,
    update_issue,
)


app = typer.Typer(help="Synchronize repository and remote state")


def _label_names(issue: Issue) -> set[str]:
    labels = issue.labels
    return {label.name for label in labels}


def _issue_needs_update(
    issue: Issue,
    *,
    title: str,
    body: str,
    labels: list[str],
    state: str | None = None,
) -> bool:
    if issue.title != title:
        return True
    if (issue.body or "") != body:
        return True
    if _label_names(issue) != set(labels):
        return True
    if state is not None and issue.state != state:
        return True
    return False


def _sync_assignees(assigned_to: str | None, authenticated_user: str | None) -> list[str] | None:
    if assigned_to is None:
        return None
    if assigned_to == authenticated_user:
        return [assigned_to]
    require_mapped_user(assigned_to)
    return [assigned_to]


@app.command("branches")
def branches() -> None:
    try:
        git.protected_branch_sync(get_branch_names())
    except (GitError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo("Protected branches synchronized.")


@app.command("status")
def status() -> None:
    branch = git.current_branch()
    dirty = git.has_uncommitted_changes()
    typer.echo(f"Project root: {PROJECT_PATHS.project_root}")
    typer.echo(f"Branch: {branch or 'detached'}")
    typer.echo(f"Uncommitted changes: {'yes' if dirty else 'no'}")


@app.command("github-user")
def github_user() -> None:
    try:
        typer.echo(authenticated_username())
    except GitHubError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error


def _sync_specs(repo: Repository, authenticated_user: str | None = None) -> int:
    actions = 0
    remote_by_number = {issue.number: issue for issue in list_issues(repo, SPEC_LABEL, state="open")}
    local_by_issue = {
        record.issue_id: record
        for record in specs.list_all()
        if record.issue_id is not None
    }

    for record in specs.list_all():
        if record.issue_id is None:
            if record.status in {"completed", "abandoned"}:
                continue
            issue = create_issue(
                repo,
                record.title,
                record.body,
                issue_labels("spec", record.status),
                _sync_assignees(record.assigned_to, authenticated_user),
            )
            specs.update_issue(record.slug, issue.number, issue.html_url)
            actions += 1
            continue

        issue = remote_by_number.get(record.issue_id)
        if issue is not None:
            labels = issue_labels("spec", record.status)
            if _issue_needs_update(issue, title=record.title, body=record.body, labels=labels):
                update_issue(
                    repo,
                    record.issue_id,
                    title=record.title,
                    body=record.body,
                    labels=labels,
                )
                actions += 1

    for issue in remote_by_number.values():
        if issue.number in local_by_issue:
            continue
        labels = [label.name for label in issue.labels]
        status_value = cast(SpecStatus, status_from_labels(labels, "spec") or "todo")
        metadata = create_spec_frontmatter(
            issue.title,
            status=status_value,
            issue_id=issue.number,
            issue_url=issue.html_url,
        )
        specs.create_with_metadata(issue.title, metadata, issue.body or "")
        actions += 1

    return actions


def _sync_todos(repo: Repository) -> int:
    actions = 0
    remote_by_number = {issue.number: issue for issue in list_issues(repo, TODO_LABEL, state="open")}
    local_by_issue = {
        record.issue_id: record
        for record in todos.list_all()
        if record.issue_id is not None
    }

    for record in todos.list_all():
        if record.issue_id is None:
            issue = create_issue(
                repo,
                record.title,
                record.body,
                issue_labels("todo", record.status),
            )
            todos.update_issue(record.slug, issue.number, issue.html_url)
            actions += 1
            continue

        issue = remote_by_number.get(record.issue_id)
        if issue is not None:
            state = "closed" if record.status == "claimed" else "open"
            labels = issue_labels("todo", record.status)
            if _issue_needs_update(issue, title=record.title, body=record.body, labels=labels, state=state):
                update_issue(
                    repo,
                    record.issue_id,
                    title=record.title,
                    body=record.body,
                    state=state,
                    labels=labels,
                )
                actions += 1

    for issue in remote_by_number.values():
        if issue.number in local_by_issue:
            continue
        labels = [label.name for label in issue.labels]
        status_value = cast(TodoStatus, status_from_labels(labels, "todo") or "open")
        metadata = create_todo_frontmatter(
            issue.title,
            issue_id=issue.number,
            issue_url=issue.html_url,
        ).model_copy(update={"status": status_value})
        todos.create_with_metadata(issue.title, metadata, issue.body or "")
        actions += 1

    return actions


def _sync_issues(repo: Repository, authenticated_user: str | None = None) -> int:
    ensure_labels(repo)
    return _sync_specs(repo, authenticated_user) + _sync_todos(repo)


@app.command("issues")
def issues() -> None:
    try:
        repo = repository()
        count = _sync_issues(repo, authenticated_username())
    except (GitHubError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Issue sync complete. Actions: {count}")


def sync_git_state() -> None:
    branches = get_branch_names()
    current = git.current_branch()
    if current is None:
        raise GitError("Could not determine current branch.")
    if git.has_uncommitted_changes():
        raise GitError("UNCOMMITTED_CHANGES")

    git.fetch()
    if worktrees.is_worktree():
        parent = branches.noswitch_branches.parent_for(current)
        if parent is not None:
            git.rebase_onto(f"origin/{parent}")
            return
        if current.startswith(f"{branches.dev}-"):
            git.rebase_onto(f"origin/{branches.dev}")
            git.push_force_with_lease(current)
            typer.echo(
                f"Spec branch rebased onto origin/{branches.dev} and pushed with --force-with-lease."
            )
            return
        raise GitError(
            f"Worktree sync only supports spec branches based on '{branches.dev}'. Current branch: {current}"
        )

    if current != branches.dev:
        raise GitError(
            f"Sync must run from '{branches.dev}' in the main repository. Current branch: {current}"
        )

    git.protected_branch_sync(branches)


def _print_git_sync_failure(error: GitError) -> None:
    message = str(error)
    branches = get_branch_names()
    if message == "UNCOMMITTED_CHANGES" or "uncommitted tracked changes" in message.lower():
        typer.echo("", err=True)
        typer.echo("=" * 60, err=True)
        typer.echo("UNCOMMITTED CHANGES - COMMIT AND PUSH FIRST", err=True)
        typer.echo("=" * 60, err=True)
        typer.echo("", err=True)
        typer.echo("Cannot sync/rebase with uncommitted changes.", err=True)
        typer.echo("", err=True)
        typer.echo("To proceed, commit and push your changes, then run sync again:", err=True)
        typer.echo("  git add -A && git commit -m '<describe what was done>' && git push", err=True)
        typer.echo("", err=True)
        typer.echo("Do not continue implementation work until sync succeeds.", err=True)
        typer.echo("=" * 60, err=True)
        return

    if "conflict" in message.lower() or "rebase" in message.lower():
        typer.echo("", err=True)
        typer.echo("=" * 60, err=True)
        typer.echo("REBASE FAILED - MANUAL INTERVENTION REQUIRED", err=True)
        typer.echo("=" * 60, err=True)
        typer.echo("", err=True)
        typer.echo("Could not automatically rebase onto the configured upstream.", err=True)
        typer.echo("", err=True)
        typer.echo("To resolve this manually from the current branch:", err=True)
        typer.echo("  1. git fetch origin", err=True)
        typer.echo(f"  2. git rebase origin/{branches.dev}", err=True)
        typer.echo("  3. Resolve any conflicts", err=True)
        typer.echo("  4. git rebase --continue", err=True)
        typer.echo("  5. git push --force-with-lease", err=True)
        typer.echo("  6. python -B .agent_core/harness/main.py sync", err=True)
        typer.echo("", err=True)
        typer.echo(f"Reason: {message}", err=True)
        typer.echo("=" * 60, err=True)
        return

    typer.echo(f"Git sync failed: {message}", err=True)


def _complete_merged_specs(repo: Repository) -> int:
    if worktrees.is_worktree():
        return 0

    branches = get_branch_names()
    current = git.current_branch()
    if current != branches.dev:
        return 0
    if git.has_uncommitted_changes():
        typer.echo(
            "Skipping merged spec completion because the working tree is dirty.",
            err=True,
        )
        return 0

    completed = 0
    for record in specs.list_all(status="merge_ready"):
        pull_number = parse_pull_number(record.pr_url or "")
        if pull_number is None:
            continue
        try:
            pull_request = repo.get_pull(pull_number)
        except Exception:
            continue
        if not getattr(pull_request, "merged", False):
            continue

        specs.update_status(record.slug, "completed")
        if record.issue_id:
            update_issue(
                repo,
                record.issue_id,
                state="closed",
                labels=issue_labels("spec", "completed"),
            )
        if record.branch:
            worktrees.remove(record.slug, force=True)
            try:
                git.delete_local_branch(record.branch, force=True)
            except GitError:
                pass
            if delete_remote_branch(repo, record.branch):
                try:
                    git.prune()
                except GitError:
                    pass
        completed += 1

    if completed:
        git.add_all()
        if git.commit(f"sync completed specs ({completed})"):
            git.push(branches.dev)

    return completed


def _cleanup_completed_spec_branches(repo: Repository) -> int:
    if worktrees.is_worktree():
        return 0

    branches = get_branch_names()
    current = git.current_branch()
    if current != branches.dev:
        return 0

    cleaned = 0
    protected = set(branches.protected)
    for record in specs.list_all(status="completed"):
        if not record.branch or record.branch in protected:
            continue
        removed_any = worktrees.remove(record.slug, force=True)
        if git.local_branch_exists(record.branch):
            try:
                git.delete_local_branch(record.branch, force=True)
                removed_any = True
            except GitError:
                pass
        if delete_remote_branch(repo, record.branch):
            removed_any = True
            try:
                git.prune()
            except GitError:
                pass
        if removed_any:
            cleaned += 1

    return cleaned


def _cleanup_closed_promotion_branches(repo: Repository) -> int:
    cleaned = 0
    owner = repo.owner.login
    try:
        refs = list(repo.get_git_matching_refs("heads/promotion/"))
    except GithubException as error:
        raise GitHubError(f"Could not list remote promotion branches: {error}") from error

    for ref in refs:
        branch = ref.ref.removeprefix("refs/heads/")
        try:
            if list(repo.get_pulls(state="open", head=f"{owner}:{branch}")):
                continue
            if not list(repo.get_pulls(state="closed", head=f"{owner}:{branch}")):
                continue
            ref.delete()
            cleaned += 1
        except GithubException as error:
            raise GitHubError(f"Could not clean promotion branch '{branch}': {error}") from error
    return cleaned


@app.command("all")
def sync_all(
    no_git: bool = typer.Option(
        False,
        "--no-git",
        help="Skip git sync, commit, and push operations.",
    ),
) -> None:
    if not no_git:
        try:
            sync_git_state()
        except GitError as error:
            _print_git_sync_failure(error)
            raise typer.Exit(code=1) from error
        except ValueError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=1) from error
        status()
    try:
        repo = repository()
        current_user = authenticated_username()
        count = _sync_issues(repo, current_user)
        if not no_git and ensure_current_user_mapping(current_user):
            typer.echo("Updated managed file: .agent_core/user_mappings.toml")
    except (GitHubError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Issue sync complete. Actions: {count}")
    try:
        completed = _complete_merged_specs(repo)
        if completed:
            typer.echo(f"Completed merged specs: {completed}")
        cleaned = _cleanup_completed_spec_branches(repo)
        if cleaned:
            typer.echo(f"Cleaned completed spec branches: {cleaned}")
        cleaned_promotions = _cleanup_closed_promotion_branches(repo)
        if cleaned_promotions:
            typer.echo(f"Cleaned closed promotion branches: {cleaned_promotions}")
    except GitHubError as error:
        typer.echo(f"Warning: could not reconcile merged work: {error}", err=True)

    if not no_git:
        try:
            git.add_all()
            if git.commit("sync agent state"):
                branch = git.current_branch()
                if branch:
                    git.push(branch)
        except GitError as error:
            typer.echo(f"Warning: could not push local state: {error}", err=True)


@app.callback(invoke_without_command=True)
def run(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        sync_all()
