from pathlib import Path

import typer
from typing_extensions import Annotated

from src.config.paths import PROJECT_PATHS
from src.state import todos
from src.utils import git
from src.utils.errors import GitError, GitHubError
from src.utils.github import create_issue, ensure_labels, issue_labels, repository
from src.utils.markdown import slugify


def _commit_and_push(path: Path, slug: str) -> None:
    staged = git.run_git(["diff", "--cached", "--quiet"], check=False)
    if staged.returncode != 0:
        typer.echo("Warning: existing staged changes found; todo was not committed.", err=True)
        return

    relative_path = path.relative_to(PROJECT_PATHS.project_root)
    git.run_git(["add", str(relative_path)])
    if not git.commit(f"add todo {slug}"):
        return

    branch = git.current_branch()
    if branch is None:
        typer.echo("Warning: could not determine current branch; todo commit was not pushed.", err=True)
        return

    git.push(branch)
    typer.echo("Committed and pushed todo state.")


def run(title: str, description: Annotated[str, typer.Argument()] = "") -> None:
    slug = slugify(title)
    if todos.get(slug) is not None:
        typer.echo(f"Todo '{slug}' already exists.", err=True)
        raise typer.Exit(code=1)

    try:
        repo = repository()
        ensure_labels(repo)
        issue = create_issue(
            repo,
            title,
            description,
            issue_labels("todo", "open"),
        )
        path = todos.create(title, description, issue_id=issue.number, issue_url=issue.html_url)
    except (GitHubError, ValueError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Created: {path}")
    typer.echo(f"Issue: {issue.html_url}")

    try:
        _commit_and_push(path, slug)
    except GitError as error:
        typer.echo(f"Warning: could not commit/push todo: {error}", err=True)
