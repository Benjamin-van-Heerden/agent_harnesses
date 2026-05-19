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

    issue_url = ""
    issue_action = ""
    checkpoint_created = False
    pushed_branch = ""
    commit_message = f"sync spec {slug}"

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
            issue_action = "Created"
            issue_url = issue.html_url
        else:
            issue = update_issue(
                repo,
                record.issue_id,
                title=record.title,
                body=record.body,
                labels=issue_labels("spec", record.status),
            )
            issue_action = "Updated"
            issue_url = issue.html_url

        git.add_all()
        if git.commit(commit_message):
            checkpoint_created = True
            branch = git.current_branch()
            if branch:
                git.push(branch)
                pushed_branch = branch

    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo("")
    typer.echo("Spec sync complete.")
    typer.echo("")
    typer.echo(f"{issue_action} GitHub issue:")
    typer.echo(f"  {issue_url}")
    if checkpoint_created:
        typer.echo("")
        typer.echo("Created a checkpoint commit containing the synced spec state:")
        typer.echo(f'  "{commit_message}"')
    else:
        typer.echo("")
        typer.echo("No checkpoint commit was needed because there were no local spec state changes.")
    if pushed_branch:
        typer.echo("")
        typer.echo(f"Pushed the checkpoint state to `{pushed_branch}`.")
    typer.echo("")
    typer.echo("Do not assign this spec unless the user explicitly gives permission.")
    typer.echo("")
    typer.echo("When the user gives permission, run:")
    typer.echo(f"  python -B .agent_core/harness/main.py spec assign {slug}")
