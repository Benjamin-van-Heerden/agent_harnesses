import typer

from src.commands.todo.utils.resolve import resolve_or_exit
from src.state import todos
from src.utils.errors import GitHubError
from src.utils.github import close_issue_with_comment, issue_labels, repository


def run(identifier: str, claimed_by: str) -> None:
    slug = resolve_or_exit(identifier)
    record = todos.get(slug)
    if record is None:
        typer.echo(f"Todo not found: {identifier}", err=True)
        raise typer.Exit(code=1)
    if record.status == "claimed":
        typer.echo(f"Todo already claimed: {record.title}", err=True)
        raise typer.Exit(code=1)

    path = todos.claim(slug, claimed_by)
    typer.echo(f"Claimed: {path}")

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
