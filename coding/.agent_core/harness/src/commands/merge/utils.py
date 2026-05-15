import typer

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
    pull_number, spec_slug = _resolve_pull_number(pr_ref)

    try:
        repo = repository()
        pull_request = repo.get_pull(pull_number)
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

        if spec_slug is not None:
            _complete_spec_after_pr_merge(repo, spec_slug)

        git.fetch()
        git.pull_ff_only(base_branch)
    except typer.Exit:
        raise
    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Merged pull request #{pull_number} into '{base_branch}'.")


def promote_branch(source: str, target: str) -> None:
    require_clean_worktree()
    require_current_branch(source)

    try:
        git.fetch()
        git.checkout(target)
        git.pull_ff_only(target)
        git.merge_ff_only(source)
        git.push(target)
    except GitError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Merged '{source}' into '{target}'.")


def _pull_number_from_ref(pr_ref: str) -> int | None:
    if pr_ref.startswith("#"):
        pr_ref = pr_ref[1:]
    if pr_ref.isdigit():
        return int(pr_ref)
    return parse_pull_number(pr_ref)


def _resolve_pull_number(pr_ref: str) -> tuple[int, str | None]:
    pull_number = _pull_number_from_ref(pr_ref)
    if pull_number is not None:
        return pull_number, None

    record = specs.get(pr_ref)
    if record is None:
        typer.echo(f"Pull request or spec not found: {pr_ref}", err=True)
        raise typer.Exit(code=1)

    pull_number = parse_pull_number(record.pr_url or "")
    if pull_number is None:
        typer.echo(f"Spec has no pull request URL: {pr_ref}", err=True)
        raise typer.Exit(code=1)

    return pull_number, record.slug


def _complete_spec_after_pr_merge(repo, spec_slug: str) -> None:
    record = specs.get(spec_slug)
    if record is None:
        return

    specs.update_status(spec_slug, "completed")
    if record.issue_id:
        update_issue(
            repo,
            record.issue_id,
            state="closed",
            labels=issue_labels("spec", "completed"),
        )

    if record.branch:
        delete_remote_branch(repo, record.branch)
        try:
            git.delete_local_branch(record.branch, force=True)
        except GitError:
            pass

    worktrees.remove(spec_slug, force=True)
