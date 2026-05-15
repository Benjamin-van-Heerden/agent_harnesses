from __future__ import annotations

import typer

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
        username = authenticated_username()
        branch = record.get("branch") or f"dev-{slugify(username)}-{slug}"
        specs.update_assignment(slug, username)
        specs.update_branch(slug, branch)

        git.add_all()
        git.commit(f"prepare spec {slug} for assignment")
        current = git.current_branch()
        if current:
            git.push(current)

        existing = [item for item in worktrees.list_all() if item.path == worktrees.path_for(slug)]
        if existing:
            typer.echo(f"Worktree already exists: {existing[0].path}")
            return

        path = worktrees.create(slug, branch)
        git.push(branch, cwd=path, set_upstream=True)

        if record.get("issue_id"):
            repo = repository()
            update_issue(repo, record["issue_id"], assignees=[username])

    except (GitError, GitHubError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Created worktree: {path}")
    typer.echo(f"Branch: {branch}")
