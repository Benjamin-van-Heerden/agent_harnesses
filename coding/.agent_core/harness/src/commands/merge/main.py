import typer

from src.config.branches import get_branch_names
from src.state import specs
from src.utils import git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.github import (
    delete_remote_branch,
    issue_labels,
    merge_pull_request,
    parse_pull_number,
    repository,
    update_issue,
)


app = typer.Typer(help="Merge pull requests")


@app.callback(invoke_without_command=True)
def run(
    spec_slug: str = typer.Argument(...),
    message: str = typer.Argument("merge completed specification"),
) -> None:
    record = specs.get(spec_slug)
    if record is None:
        typer.echo(f"Spec not found: {spec_slug}", err=True)
        raise typer.Exit(code=1)
    pull_number = parse_pull_number(record.pr_url or "")
    if pull_number is None:
        typer.echo("Spec has no pull request URL.", err=True)
        raise typer.Exit(code=1)

    try:
        repo = repository()
        result = merge_pull_request(repo, pull_number, message)
        if not getattr(result, "merged", False):
            typer.echo("Pull request was not merged.", err=True)
            raise typer.Exit(code=1)

        specs.update_status(spec_slug, "completed")
        if record.issue_id:
            update_issue(
                repo,
                record.issue_id,
                state="closed",
                labels=issue_labels("spec", "completed"),
            )

        branch = record.branch
        if branch:
            delete_remote_branch(repo, branch)
            try:
                git.delete_local_branch(branch, force=True)
            except GitError:
                pass

        worktrees.remove(spec_slug, force=True)
        git.checkout(get_branch_names().dev)
        git.pull_ff_only(get_branch_names().dev)
    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Merged and cleaned up: {spec_slug}")
