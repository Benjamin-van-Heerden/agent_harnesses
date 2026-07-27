import re

import typer
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
from src.state import specs
from src.utils.errors import GitHubError
from src.utils.github import parse_pull_number, repository

PROMOTION_BRANCH_PREFIX = "promotion/"


def pull_number_from_ref(pr_ref: str) -> int | None:
    normalized = pr_ref.removeprefix("#")
    if normalized.isdigit():
        return int(normalized)
    return parse_pull_number(normalized)


def resolve_pull_number(pr_ref: str) -> int:
    pull_number = pull_number_from_ref(pr_ref)
    if pull_number is not None:
        return pull_number
    record = specs.get(pr_ref)
    pull_number = parse_pull_number(record.pr_url or "") if record is not None else None
    if pull_number is None:
        typer.echo(f"Pull request or spec not found: {pr_ref}", err=True)
        raise typer.Exit(code=1)
    return pull_number


def get_pull_request(pr_ref: str) -> tuple[Repository, PullRequest]:
    try:
        repo = repository()
        return repo, repo.get_pull(resolve_pull_number(pr_ref))
    except (GitHubError, GithubException) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error


def is_promotion_pull_request(pull_request: PullRequest) -> bool:
    return pull_request.head.ref.startswith(PROMOTION_BRANCH_PREFIX)


def promotion_target_from_branch(branch: str) -> str | None:
    match = re.fullmatch(r"promotion/([^/]+)/[^/]+", branch)
    return match.group(1) if match is not None else None
