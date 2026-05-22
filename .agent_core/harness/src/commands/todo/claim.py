import typer

from src.commands.todo.utils.context import require_dev_main_repo
from src.commands.todo.utils.resolve import resolve_or_exit
from src.state import todos
from src.utils import git
from src.utils.errors import GitError, GitHubError
from src.utils.github import close_issue_with_comment, issue_labels, repository


def run(identifier: str, claimed_by: str) -> None:
    branch = require_dev_main_repo("claim todos")
    slug = resolve_or_exit(identifier)
    record = todos.get(slug)
    if record is None:
        typer.echo(f"Todo not found: {identifier}", err=True)
        raise typer.Exit(code=1)
    if record.status == "claimed":
        typer.echo(f"Todo already claimed: {record.title}", err=True)
        raise typer.Exit(code=1)

    try:
        if git.has_uncommitted_changes():
            typer.echo("Todo claim stopped before changing state.", err=True)
            typer.echo("Reason: the working tree has pre-existing uncommitted changes.", err=True)
            typer.echo("You must commit, push, or otherwise resolve existing changes before claiming a todo.", err=True)
            raise typer.Exit(code=1)
    except GitError as error:
        typer.echo("Todo claim stopped before changing state.", err=True)
        typer.echo(f"Reason: {error}", err=True)
        raise typer.Exit(code=1) from error

    path = todos.claim(slug, claimed_by)
    typer.echo(f"Claimed: {path}")

    try:
        git.add_all()
        if not git.commit(f"claim todo {slug}"):
            typer.echo("Todo claim did not produce a git commit.", err=True)
            raise typer.Exit(code=1)
        git.push(branch)
        typer.echo(f"Committed and pushed todo claim to {branch}.")
    except GitError as error:
        typer.echo("Todo claim was written locally but could not be published.", err=True)
        typer.echo(f"Reason: {error}", err=True)
        typer.echo("You must resolve the git failure before the linked GitHub issue is closed.", err=True)
        raise typer.Exit(code=1) from error

    if record.issue_id is None:
        return

    try:
        repo = repository()
        close_issue_with_comment(
            repo,
            record.issue_id,
            f"Todo claimed by {claimed_by} via `todo claim`.",
            labels=issue_labels("todo", "claimed"),
        )
        typer.echo(f"Closed issue: #{record.issue_id}")
    except GitHubError as error:
        typer.echo(f"Warning: could not close linked GitHub issue: {error}", err=True)
