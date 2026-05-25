import typer
from github.PullRequest import PullRequest
from github.Repository import Repository

from src.config.branches import get_branch_names
from src.state import specs
from src.state.models import Spec
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


def require_clean_worktree() -> None:
    if git.has_uncommitted_changes():
        typer.echo("Working tree has uncommitted changes.", err=True)
        raise typer.Exit(code=1)


def require_current_branch(branch: str) -> None:
    current = git.current_branch()
    if current != branch:
        typer.echo(
            f"Must be on '{branch}' branch. Currently on '{current or 'detached HEAD'}'.",
            err=True,
        )
        raise typer.Exit(code=1)


def list_pull_requests(base_branch: str) -> None:
    try:
        repo = repository()
        pull_requests = list(repo.get_pulls(state="open", base=base_branch))
    except GitHubError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    if not pull_requests:
        typer.echo(f"No open pull requests targeting '{base_branch}'.")
        return

    typer.echo(f"Open pull requests targeting '{base_branch}':")
    for pull_request in pull_requests:
        marker = "mergeable" if pull_request.mergeable is not False else "blocked"
        typer.echo(
            f"  #{pull_request.number} {pull_request.title} "
            f"({pull_request.head.ref} -> {pull_request.base.ref}, {marker})"
        )


def merge_pull_request_into_base(
    pr_ref: str,
    base_branch: str,
    message: str | None,
) -> None:
    pull_number = _resolve_pull_number(pr_ref)
    branches = get_branch_names()

    try:
        repo = repository()
        pull_request = repo.get_pull(pull_number)
        record = _resolve_spec_for_pull_request(pull_request)
        if pull_request.base.ref != base_branch:
            typer.echo(
                f"Pull request #{pull_number} targets '{pull_request.base.ref}', not '{base_branch}'.",
                err=True,
            )
            raise typer.Exit(code=1)

        result = merge_pull_request(
            repo,
            pull_number,
            message or getattr(pull_request, "title", "") or f"merge pull request #{pull_number}",
        )
        if not getattr(result, "merged", False):
            typer.echo("Pull request was not merged.", err=True)
            raise typer.Exit(code=1)

        git.fetch()
        git.checkout(base_branch)
        git.pull_ff_only(base_branch)

        if record is not None:
            _complete_spec_after_pr_merge_locally(record, base_branch)
            _complete_spec_after_pr_merge_remotely(repo, record)
        else:
            typer.echo(
                "Warning: merged PR, but no matching local spec was found for cleanup.",
                err=True,
            )
        if base_branch != branches.dev:
            git.checkout(branches.dev)
    except typer.Exit:
        if git.current_branch() != branches.dev:
            git.checkout(branches.dev)
        raise
    except (GitError, GitHubError) as error:
        if git.current_branch() != branches.dev:
            git.checkout(branches.dev)
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Merged pull request #{pull_number} into '{base_branch}'.")
    if git.current_branch() == branches.dev:
        typer.echo(f"Returned to '{branches.dev}'.")


def promote_branch(source: str, target: str) -> None:
    branches = get_branch_names()
    require_clean_worktree()
    require_current_branch(branches.dev)

    try:
        git.fetch()
        git.checkout(source)
        git.pull_ff_only(source)
        git.checkout(target)
        git.pull_ff_only(target)
        git.merge_ff_only(source)
        git.push(target)
        git.checkout(branches.dev)
    except GitError as error:
        git.checkout(branches.dev)
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Merged '{source}' into '{target}'.")
    typer.echo(f"Returned to '{branches.dev}'.")


def dry_run_promote_branch(source: str, target: str) -> None:
    branches = get_branch_names()
    require_clean_worktree()
    require_current_branch(branches.dev)
    typer.echo(f"Dry run: merge '{source}' into '{target}'.")
    typer.echo("")
    typer.echo("Would perform the following steps:")
    typer.echo(f"1. Confirm the working tree is clean on '{branches.dev}'.")
    typer.echo("2. Fetch latest changes from origin.")
    typer.echo(f"3. Switch to '{source}' and pull latest.")
    typer.echo(f"4. Switch to '{target}' and pull latest.")
    typer.echo(f"5. Merge '{source}' into '{target}' with fast-forward only.")
    typer.echo(f"6. Push '{target}' to origin.")
    typer.echo(f"7. Return to '{branches.dev}'.")


def _pull_number_from_ref(pr_ref: str) -> int | None:
    if pr_ref.startswith("#"):
        pr_ref = pr_ref[1:]
    if pr_ref.isdigit():
        return int(pr_ref)
    return parse_pull_number(pr_ref)


def _resolve_pull_number(pr_ref: str) -> int:
    pull_number = _pull_number_from_ref(pr_ref)
    if pull_number is not None:
        return pull_number

    record = specs.get(pr_ref)
    if record is None:
        typer.echo(f"Pull request or spec not found: {pr_ref}", err=True)
        raise typer.Exit(code=1)

    pull_number = parse_pull_number(record.pr_url or "")
    if pull_number is None:
        typer.echo(f"Spec has no pull request URL: {pr_ref}", err=True)
        raise typer.Exit(code=1)

    return pull_number


def _resolve_spec_for_pull_request(pull_request: PullRequest) -> Spec | None:
    for record in specs.list_all():
        if record.pr_url == pull_request.html_url:
            return record
        if record.branch == pull_request.head.ref:
            return record
    return None


def _complete_spec_after_pr_merge_locally(record: Spec, base_branch: str) -> None:
    typer.echo(f"Completing local spec state: {record.slug}")
    specs.update_status(record.slug, "completed")
    worktrees.remove(record.slug, force=True)
    if record.branch:
        try:
            git.delete_local_branch(record.branch, force=True)
        except GitError:
            pass

    git.add_all()
    if git.commit(f"complete spec {record.slug}"):
        git.push(base_branch)
        typer.echo(f"Pushed completed spec state to '{base_branch}'.")


def _complete_spec_after_pr_merge_remotely(repo: Repository, record: Spec) -> None:
    typer.echo(f"Cleaning up remote spec state: {record.slug}")
    if record.issue_id:
        update_issue(
            repo,
            record.issue_id,
            state="closed",
            labels=issue_labels("spec", "completed"),
        )

    if record.branch:
        if delete_remote_branch(repo, record.branch):
            try:
                git.prune()
            except GitError:
                pass
