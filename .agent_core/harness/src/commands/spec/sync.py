import typer

from src.state import specs
from src.utils import git
from src.utils.errors import GitError, GitHubError
from src.utils.github import create_issue, issue_labels, repository, update_issue


def run(slug: str) -> None:
    record = specs.get(slug)
    if record is None:
        typer.echo(f"Spec not found: {slug}", err=True)
        raise typer.Exit(code=1)

    try:
        repo = repository()
        if record.issue_id is None:
            issue = create_issue(
                repo,
                record.title,
                record.body,
                issue_labels("spec", record.status),
                [record.assigned_to] if record.assigned_to else None,
            )
            specs.update_issue(record.slug, issue.number, issue.html_url)
            typer.echo(f"Created GitHub issue: {issue.html_url}")
        else:
            issue = update_issue(
                repo,
                record.issue_id,
                title=record.title,
                body=record.body,
                labels=issue_labels("spec", record.status),
            )
            typer.echo(f"Updated GitHub issue: {issue.html_url}")

        git.add_all()
        if git.commit(f"sync spec {slug}"):
            branch = git.current_branch()
            if branch:
                git.push(branch)
                typer.echo(f"Pushed synced spec state to `{branch}`.")

    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo("")
    typer.echo("Spec sync complete.")
    typer.echo("")
    typer.echo("Next step:")
    typer.echo(f"  python -B .agent_core/harness/main.py spec assign {slug}")
