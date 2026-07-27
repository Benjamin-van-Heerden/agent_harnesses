import time
from typing import Annotated

import typer
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
from src.commands.pr.utils import (
    get_pull_request,
    is_promotion_pull_request,
    promotion_target_from_branch,
)
from src.config.branches import get_branch_names
from src.state import specs
from src.state.models import Spec
from src.utils import git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.github import (
    delete_remote_branch,
    issue_labels,
    squash_pull_request,
    update_issue,
)


def _require_clean_worktree() -> None:
    if git.has_uncommitted_changes():
        typer.echo("Working tree has uncommitted changes.", err=True)
        raise typer.Exit(code=1)


def _require_current_branch(branch: str) -> None:
    current = git.current_branch()
    if current != branch:
        typer.echo(
            f"Must be on '{branch}' branch. Currently on '{current or 'detached HEAD'}'.",
            err=True,
        )
        raise typer.Exit(code=1)


def _require_production_confirmation(pull_request: PullRequest, force: bool) -> None:
    branches = get_branch_names()
    if pull_request.base.ref != branches.main or force:
        return
    typer.echo("PRODUCTION PROMOTION CONFIRMATION REQUIRED", err=True)
    typer.echo("", err=True)
    typer.echo(
        f"Pull request: #{pull_request.number} {pull_request.title}",
        err=True,
    )
    typer.echo(
        f"Route: {pull_request.head.ref} → {branches.main}",
        err=True,
    )
    typer.echo("", err=True)
    typer.echo(
        f'You must ask the user: "Are you sure you want to promote PR #{pull_request.number} into production?"',
        err=True,
    )
    typer.echo("Do not run the command below until the user explicitly confirms:", err=True)
    typer.echo(
        f"  python -B .agent_core/harness/main.py pr merge {pull_request.number} --force",
        err=True,
    )
    raise typer.Exit(code=1)


def _merge_promotion(repo: Repository, pull_request: PullRequest) -> None:
    branches = get_branch_names()
    head = pull_request.head.ref
    base = pull_request.base.ref
    expected_target = promotion_target_from_branch(head)
    if expected_target != base or base not in {branches.test, branches.main}:
        typer.echo(
            f"Promotion branch '{head}' does not match pull request target '{base}'.",
            err=True,
        )
        raise typer.Exit(code=1)
    if pull_request.state != "open":
        typer.echo(f"Pull request #{pull_request.number} is not open.", err=True)
        raise typer.Exit(code=1)
    if pull_request.draft:
        typer.echo(f"Pull request #{pull_request.number} is still a draft.", err=True)
        raise typer.Exit(code=1)
    if pull_request.mergeable is False:
        typer.echo(f"Pull request #{pull_request.number} is not mergeable.", err=True)
        raise typer.Exit(code=1)
    try:
        commits = list(pull_request.get_commits())
        if commits:
            head_commit = commits[-1]
            combined_status = head_commit.get_combined_status()
            check_runs = list(head_commit.get_check_runs())
            if combined_status.total_count and combined_status.state != "success":
                typer.echo(
                    f"Pull request #{pull_request.number} has non-successful commit statuses: {combined_status.state}.",
                    err=True,
                )
                raise typer.Exit(code=1)
            incomplete = [
                check_run.name
                for check_run in check_runs
                if check_run.status != "completed"
                or check_run.conclusion not in {"success", "neutral", "skipped"}
            ]
            if incomplete:
                typer.echo(
                    f"Pull request #{pull_request.number} has incomplete or unsuccessful checks:",
                    err=True,
                )
                for name in incomplete:
                    typer.echo(f"  - {name}", err=True)
                raise typer.Exit(code=1)

        latest_reviews: dict[str, str] = {}
        for review in pull_request.get_reviews():
            latest_reviews[review.user.login] = review.state
        approving_reviewers = [
            user for user, state in latest_reviews.items() if state == "APPROVED"
        ]
        blocking_reviewers = [
            user for user, state in latest_reviews.items() if state == "CHANGES_REQUESTED"
        ]
        if blocking_reviewers:
            typer.echo(
                f"Pull request #{pull_request.number} has outstanding change requests from: "
                + ", ".join(sorted(blocking_reviewers)),
                err=True,
            )
            raise typer.Exit(code=1)
        if not approving_reviewers:
            typer.echo(
                f"Pull request #{pull_request.number} has no current approving review.",
                err=True,
            )
            raise typer.Exit(code=1)
    except GithubException as error:
        typer.echo(f"Could not verify pull request checks and reviews: {error}", err=True)
        raise typer.Exit(code=1) from error

    try:
        git.fetch()
        remote_base = f"origin/{base}"
        remote_head = f"origin/{head}"
        if not git.is_ancestor(remote_base, remote_head):
            raise GitError(
                f"Promotion is no longer a fast-forward: {remote_base} is not an ancestor of {remote_head}."
            )
        git.push_ref(remote_head, base)
        git.fetch()
        for _attempt in range(5):
            pull_request.update()
            if pull_request.merged:
                break
            time.sleep(1)
        if pull_request.merged:
            delete_remote_branch(repo, head)
            typer.echo(f"Merged promotion pull request #{pull_request.number} into '{base}' with a fast-forward.")
            typer.echo(f"Deleted remote promotion branch: {head}")
            return
        typer.echo(
            f"Fast-forwarded '{base}', but GitHub has not yet reported pull request #{pull_request.number} as merged.",
            err=True,
        )
        typer.echo("The remote promotion branch was retained for sync cleanup.", err=True)
    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error


def _spec_for_pull_request(pull_request: PullRequest) -> Spec | None:
    for record in specs.list_all():
        if record.pr_url == pull_request.html_url:
            return record
        if record.branch == pull_request.head.ref:
            return record
    return None


def _complete_spec_locally(record: Spec, base_branch: str) -> None:
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


def _complete_spec_remotely(repo: Repository, record: Spec) -> None:
    typer.echo(f"Cleaning up remote spec state: {record.slug}")
    if record.issue_id:
        update_issue(
            repo,
            record.issue_id,
            state="closed",
            labels=issue_labels("spec", "completed"),
        )

    if record.branch and delete_remote_branch(repo, record.branch):
        try:
            git.prune()
        except GitError:
            pass


def _merge_normal_pull_request(
    repo: Repository,
    pull_request: PullRequest,
    message: str | None,
) -> None:
    branches = get_branch_names()
    base = pull_request.base.ref
    record = _spec_for_pull_request(pull_request)
    try:
        result = squash_pull_request(
            pull_request,
            message or pull_request.title or f"merge pull request #{pull_request.number}",
        )
        if not result.merged:
            typer.echo("Pull request was not merged.", err=True)
            raise typer.Exit(code=1)

        git.fetch()
        git.checkout(base)
        git.pull_ff_only(base)

        if record is not None:
            _complete_spec_locally(record, base)
            _complete_spec_remotely(repo, record)
        else:
            typer.echo("Warning: merged PR, but no matching local spec was found for cleanup.", err=True)
        if base != branches.dev:
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

    typer.echo(f"Merged pull request #{pull_request.number} into '{base}'.")
    if git.current_branch() == branches.dev:
        typer.echo(f"Returned to '{branches.dev}'.")


def run(
    pr_ref: Annotated[str, typer.Argument(help="PR number, URL, or spec slug")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Required after explicit user confirmation for merges into the production branch.",
        ),
    ] = False,
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Commit message for a normal pull request squash merge"),
    ] = None,
) -> None:
    repo, pull_request = get_pull_request(pr_ref)
    branches = get_branch_names()
    if not is_promotion_pull_request(pull_request) and pull_request.base.ref in {
        branches.test,
        branches.main,
    }:
        typer.echo(
            f"Protected branch '{pull_request.base.ref}' only accepts harness-managed promotion pull requests.",
            err=True,
        )
        raise typer.Exit(code=1)
    _require_production_confirmation(pull_request, force)
    _require_clean_worktree()
    _require_current_branch(branches.dev)
    if is_promotion_pull_request(pull_request):
        _merge_promotion(repo, pull_request)
        return
    _merge_normal_pull_request(repo, pull_request, message)
