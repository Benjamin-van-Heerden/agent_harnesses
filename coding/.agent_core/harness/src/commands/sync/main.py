from typing import cast

import typer

from src.config.branches import get_branch_names
from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import SpecStatus, TodoStatus, create_spec_frontmatter, create_todo_frontmatter
from src.state import specs, todos
from src.utils import git
from src.utils.errors import GitError, GitHubError
from src.utils.github import (
    SPEC_LABEL,
    TODO_LABEL,
    authenticated_username,
    create_issue,
    ensure_labels,
    issue_labels,
    list_issues,
    repository,
    status_from_labels,
    update_issue,
)


app = typer.Typer(help="Synchronize repository and remote state")


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


def _sync_specs(repo) -> int:
    actions = 0
    remote_by_number = {issue.number: issue for issue in list_issues(repo, SPEC_LABEL, state="open")}
    local_by_issue = {
        record.issue_id: record
        for record in specs.list_all()
        if record.issue_id is not None
    }

    for record in specs.list_all():
        if record.issue_id is None:
            issue = create_issue(
                repo,
                record.title,
                record.body,
                issue_labels("spec", record.status),
                [record.assigned_to] if record.assigned_to else None,
            )
            specs.update_issue(record.slug, issue.number, issue.html_url)
            actions += 1
            continue

        issue = remote_by_number.get(record.issue_id)
        if issue is not None:
            update_issue(
                repo,
                record.issue_id,
                title=record.title,
                body=record.body,
                labels=issue_labels("spec", record.status),
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


def _sync_todos(repo) -> int:
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
            update_issue(
                repo,
                record.issue_id,
                title=record.title,
                body=record.body,
                state="closed" if record.status == "claimed" else "open",
                labels=issue_labels("todo", record.status),
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


@app.command("issues")
def issues() -> None:
    try:
        repo = repository()
        ensure_labels(repo)
        count = _sync_specs(repo) + _sync_todos(repo)
    except GitHubError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Issue sync complete. Actions: {count}")


def sync_git_state() -> None:
    git.sync_current_branch(get_branch_names())


@app.command("all")
def sync_all(no_git: bool = False) -> None:
    if not no_git:
        try:
            sync_git_state()
        except (GitError, ValueError) as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=1) from error
        status()
    issues()
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
