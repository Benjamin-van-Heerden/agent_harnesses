from __future__ import annotations

import typer
from typing_extensions import Annotated

from src.config.branches import get_branch_names
from src.state import specs
from src.state import tasks
from src.utils import git
from src.utils.errors import GitError, GitHubError
from src.utils.github import create_pull_request, issue_labels, repository, update_issue


def run(
    slug: str,
    message: Annotated[str, typer.Argument()] = "complete spec",
) -> None:
    record = specs.get(slug)
    if record is None:
        typer.echo(f"Spec not found: {slug}", err=True)
        raise typer.Exit(code=1)

    incomplete = [item for item in tasks.list_all(slug) if item.status != "completed"]
    if incomplete:
        typer.echo("Cannot complete spec with incomplete tasks:", err=True)
        for item in incomplete:
            typer.echo(f"  - {item.title}", err=True)
        raise typer.Exit(code=1)

    branch = record.branch or git.current_branch()
    if branch is None:
        typer.echo("Could not determine branch for spec.", err=True)
        raise typer.Exit(code=1)

    try:
        git.add_all()
        git.commit(message)
        git.push(branch)
        git.fetch_origin()
        git.rebase_onto(f"origin/{get_branch_names().dev}")
        git.push_force_with_lease(branch)

        specs.update_status(slug, "merge_ready")
        updated = specs.get(slug) or record

        if updated.issue_id:
            repo = repository()
            update_issue(
                repo,
                updated.issue_id,
                labels=issue_labels("spec", "merge_ready"),
            )
            pull_request = create_pull_request(
                repo,
                f"[Complete]: {updated.title}",
                f"Completes specification: {updated.title}\n\nCloses #{updated.issue_id}",
                branch,
                get_branch_names().dev,
            )
            specs.update_pr(slug, pull_request.html_url)
            git.add_all()
            if git.commit(f"record pull request for {slug}"):
                git.push_force_with_lease(branch)
            typer.echo(f"Pull request: {pull_request.html_url}")

    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Marked merge ready: {slug}")
