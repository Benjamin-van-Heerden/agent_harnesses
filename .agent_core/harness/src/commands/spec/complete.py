import typer
from src.config.branches import get_branch_names
from src.state import logs, specs, tasks
from src.utils import git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.github import create_pull_request, issue_labels, repository, update_issue
from typing_extensions import Annotated


def _require_active_spec_worktree(slug: str, branch: str | None) -> None:
    current = git.current_branch()
    if branch is None:
        typer.echo(f"Error: Spec '{slug}' has no branch. Assign it first.", err=True)
        raise typer.Exit(code=1)
    if not worktrees.is_worktree():
        typer.echo("Error: Spec completion must run from its worktree.", err=True)
        typer.echo(
            "Run this command from the assigned spec worktree directory.", err=True
        )
        raise typer.Exit(code=1)
    if current != branch:
        typer.echo(f"Error: Spec '{slug}' is not currently active.", err=True)
        typer.echo(f"Expected branch: {branch}", err=True)
        typer.echo(f"Current branch: {current or 'detached HEAD'}", err=True)
        typer.echo("To complete this spec, run from its worktree.", err=True)
        raise typer.Exit(code=1)


def _require_work_log(slug: str) -> None:
    if logs.list_all(limit=1, spec_slug=slug):
        return

    typer.echo(f"Error: Cannot complete spec '{slug}'. No work logs found.", err=True)
    typer.echo("", err=True)
    typer.echo("At least one work log is required before completing a spec.", err=True)
    typer.echo("Create a work log with:", err=True)
    typer.echo("  python -B .agent_core/harness/main.py log new", err=True)
    raise typer.Exit(code=1)


def _print_rebase_failure(slug: str, message: str) -> None:
    branches = get_branch_names()
    typer.echo("", err=True)
    typer.echo("=" * 60, err=True)
    typer.echo("REBASE FAILED - MANUAL INTERVENTION REQUIRED", err=True)
    typer.echo("=" * 60, err=True)
    typer.echo("", err=True)
    typer.echo(
        "Your changes were pushed to the remote spec branch before the rebase.",
        err=True,
    )
    typer.echo("", err=True)
    typer.echo("To resolve this manually:", err=True)
    typer.echo("  1. git fetch origin", err=True)
    typer.echo(f"  2. git rebase origin/{branches.dev}", err=True)
    typer.echo("  3. Resolve any conflicts", err=True)
    typer.echo("  4. git rebase --continue", err=True)
    typer.echo("  5. git push --force-with-lease", err=True)
    typer.echo(
        f'  6. Run `python -B .agent_core/harness/main.py spec complete {slug} "detailed commit message"` again',
        err=True,
    )
    typer.echo("", err=True)
    typer.echo(f"Reason: {message}", err=True)
    typer.echo("=" * 60, err=True)


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

    _require_active_spec_worktree(slug, record.branch)
    _require_work_log(slug)
    if record.issue_id is None:
        typer.echo(f"Error: Spec '{slug}' is not synced to GitHub.", err=True)
        typer.echo(
            f"Run `python -B .agent_core/harness/main.py spec sync {slug}` before completing it.",
            err=True,
        )
        raise typer.Exit(code=1)

    branch = record.branch
    if branch is None:
        typer.echo(f"Error: Spec '{slug}' has no branch. Assign it first.", err=True)
        raise typer.Exit(code=1)
    branches = get_branch_names()

    try:
        typer.echo(f"Completing spec: {record.title}")
        typer.echo("Committing changes...")
        git.add_all()
        git.commit(message)
        typer.echo("Pushing to origin to save your work...")
        git.push(branch)
        typer.echo(f"Fetching origin and rebasing onto origin/{branches.dev}...")
        git.fetch_origin()
        try:
            git.rebase_onto(f"origin/{branches.dev}")
        except GitError as error:
            git.run_git(["rebase", "--abort"], check=False)
            _print_rebase_failure(slug, str(error))
            raise typer.Exit(code=1) from error

        typer.echo("Pushing rebased branch...")
        git.push_force_with_lease(branch)

        repo = repository()
        typer.echo("Creating pull request...")
        pull_request = create_pull_request(
            repo,
            f"[Complete]: {record.title}",
            f"Completes specification: {record.title}\n\nCloses #{record.issue_id}",
            branch,
            branches.dev,
        )

        specs.update_status(slug, "merge_ready")
        specs.update_pr(slug, pull_request.html_url)
        git.add_all()
        if git.commit(f"record pull request for {slug}"):
            git.push_force_with_lease(branch)

        update_issue(
            repo,
            record.issue_id,
            labels=issue_labels("spec", "merge_ready"),
        )
        typer.echo(f"Pull request: {pull_request.html_url}")

    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo("")
    typer.echo(f"Spec '{slug}' marked as merge ready.")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo(f"1. Return to the main repository `{branches.dev}` branch.")
    typer.echo("2. Merge the PR with:")
    typer.echo(
        f"   python -B .agent_core/harness/main.py merge pr {pull_request.html_url}"
    )
    typer.echo("")
    typer.echo(
        f"You must tell the user to return to the main repository's mission-control branch (`{branches.dev}`) and run the merge command above to bring in these changes. Relay the full command."
    )
