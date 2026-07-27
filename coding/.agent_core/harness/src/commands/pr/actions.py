from pathlib import Path
from typing import Annotated

import typer
from github.GithubException import GithubException
from src.commands.pr.utils import get_pull_request


def _body(path: Path) -> str:
    if not path.is_file():
        typer.echo(f"Review response file not found: {path}", err=True)
        raise typer.Exit(code=1)
    body = path.read_text().strip()
    if not body:
        typer.echo(f"Review response file is empty: {path}", err=True)
        raise typer.Exit(code=1)
    return body


def comment(
    pr_ref: Annotated[str, typer.Argument(help="PR number, URL, or spec slug")],
    file: Annotated[Path, typer.Option("--file", help="Markdown file containing the comment")],
) -> None:
    _repo, pull_request = get_pull_request(pr_ref)
    try:
        pull_request.create_issue_comment(_body(file))
    except GithubException as error:
        typer.echo(f"Could not comment on pull request #{pull_request.number}: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Commented on pull request #{pull_request.number}.")


def _submit_review(pr_ref: str, file: Path, event: str) -> None:
    _repo, pull_request = get_pull_request(pr_ref)
    try:
        pull_request.create_review(body=_body(file), event=event)
    except GithubException as error:
        typer.echo(f"Could not submit review for pull request #{pull_request.number}: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Submitted {event.lower().replace('_', ' ')} review for pull request #{pull_request.number}.")


def approve(
    pr_ref: Annotated[str, typer.Argument(help="PR number, URL, or spec slug")],
    file: Annotated[Path, typer.Option("--file", help="Markdown file containing the approval")],
) -> None:
    _submit_review(pr_ref, file, "APPROVE")


def request_changes(
    pr_ref: Annotated[str, typer.Argument(help="PR number, URL, or spec slug")],
    file: Annotated[Path, typer.Option("--file", help="Markdown file containing the requested changes")],
) -> None:
    _submit_review(pr_ref, file, "REQUEST_CHANGES")
