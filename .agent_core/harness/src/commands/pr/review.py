from pathlib import Path
from typing import Annotated

import typer
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from src.commands.pr.utils import get_pull_request, is_promotion_pull_request
from src.config.branches import get_branch_names
from src.config.paths import PROJECT_PATHS
from src.utils.errors import GitHubError
from src.utils.github import repository


def _login(value: object) -> str:
    return str(getattr(value, "login", "unknown"))


def _kind(pull_request: PullRequest) -> str:
    return "promotion" if is_promotion_pull_request(pull_request) else "pull request"


def _review_context(pull_request: PullRequest) -> str:
    lines = [
        "# Pull Request Review Context",
        "",
        f"- Pull request: #{pull_request.number} {pull_request.title}",
        f"- URL: {pull_request.html_url}",
        f"- Author: {_login(pull_request.user)}",
        f"- Route: `{pull_request.head.ref}` → `{pull_request.base.ref}`",
        f"- Kind: {_kind(pull_request)}",
        f"- Draft: {'yes' if pull_request.draft else 'no'}",
        f"- Mergeable state: {pull_request.mergeable_state}",
        "",
        "## Pull request description",
        "",
        str(pull_request.body or "_No pull request description was provided._"),
        "",
        "## Reviews",
        "",
    ]
    reviews = list(pull_request.get_reviews())
    if reviews:
        for review in reviews:
            lines.append(
                f"- {_login(getattr(review, 'user', None))}: {getattr(review, 'state', 'UNKNOWN')} — "
                f"{getattr(review, 'body', '') or 'No review message.'}"
            )
    else:
        lines.append("_No reviews have been submitted._")

    lines.extend(["", "## General comments", ""])
    comments = list(pull_request.get_issue_comments())
    if comments:
        for comment in comments:
            lines.append(f"- {_login(getattr(comment, 'user', None))}: {getattr(comment, 'body', '')}")
    else:
        lines.append("_No general comments._")

    lines.extend(["", "## Inline review comments", ""])
    inline_comments = list(pull_request.get_review_comments())
    if inline_comments:
        for comment in inline_comments:
            location = f"{comment.path}:{comment.line}" if comment.line is not None else comment.path
            lines.append(f"- `{location}` — {_login(comment.user)}: {comment.body}")
    else:
        lines.append("_No inline review comments._")

    lines.extend(["", "## Commits and checks", ""])
    commits = list(pull_request.get_commits())
    if commits:
        for commit in commits:
            message = commit.commit.message.splitlines()[0]
            lines.append(f"- `{commit.sha[:12]}` {message}")
        head_commit = commits[-1]
        combined_status = head_commit.get_combined_status()
        lines.append(f"- Combined commit status: {combined_status.state}")
        check_runs = list(head_commit.get_check_runs())
        if check_runs:
            for check_run in check_runs:
                lines.append(
                    f"- Check `{check_run.name}`: {check_run.status}"
                    + (f" / {check_run.conclusion}" if check_run.conclusion else "")
                )
        else:
            lines.append("- No check runs were reported.")
    else:
        lines.append("_No commits were reported._")

    lines.extend(["", "## Changed files", ""])
    files = list(pull_request.get_files())
    if not files:
        lines.append("_No changed files._")
    for changed_file in files:
        lines.append(
            f"### `{changed_file.filename}` ({getattr(changed_file, 'status', 'modified')}, "
            f"+{getattr(changed_file, 'additions', 0)}/-{getattr(changed_file, 'deletions', 0)})"
        )
        patch = str(getattr(changed_file, "patch", "") or "")
        if patch:
            lines.extend(["", "```diff", patch, "```"])

    lines.extend(
        [
            "",
            "## Agent instructions",
            "",
            "You must treat the pull request body as a guide, not as proof.",
            "Inspect the actual diff and relevant source files, verify material claims, and prioritize correctness, regressions, security, data integrity, and missing tests.",
            "Report findings before offering approval or merge actions.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_context(pull_request: PullRequest) -> Path:
    temp_dir = PROJECT_PATHS.state_root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    path = temp_dir / f"pr_review_{pull_request.number}.md"
    path.write_text(_review_context(pull_request))
    return path


def _discover() -> None:
    try:
        repo = repository()
        pull_requests = list(repo.get_pulls(state="open"))
    except (GitHubError, GithubException) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    if not pull_requests:
        typer.echo("No open pull requests were found.")
        return

    branches = get_branch_names()
    typer.echo("OPEN PULL REQUESTS")
    typer.echo("")
    for pull_request in pull_requests:
        kind = "promotion" if is_promotion_pull_request(pull_request) else "pull request"
        production = " | production confirmation required" if pull_request.base.ref == branches.main else ""
        typer.echo(
            f"  #{pull_request.number} [{kind}] {pull_request.title}\n"
            f"     {_login(pull_request.user)} | {pull_request.head.ref} → {pull_request.base.ref}{production}"
        )
    typer.echo("")
    typer.echo("No pull request has been selected.")
    typer.echo("")
    typer.echo("You must tell the user that the harness can load a PR for review, submit comments, approve it, request changes, or merge it after review.")
    typer.echo("You must tell the user that a merge into the production branch requires separate explicit confirmation.")
    typer.echo("You must ask the user which pull request they mean.")
    typer.echo("Do not select or review a pull request until the user answers.")
    typer.echo("")
    typer.echo("After the user identifies a pull request, run:")
    typer.echo("  python -B .agent_core/harness/main.py pr review <PR_NUMBER_OR_URL>")


def run(
    pr_ref: Annotated[
        str | None,
        typer.Argument(help="PR number, URL, or spec slug. Omit to discover open PRs."),
    ] = None,
) -> None:
    if pr_ref is None:
        _discover()
        return
    _repo, pull_request = get_pull_request(pr_ref)
    try:
        path = _write_context(pull_request)
    except Exception as error:
        typer.echo(f"Could not build review context: {error}", err=True)
        raise typer.Exit(code=1) from error

    relative = path.relative_to(PROJECT_PATHS.project_root)
    typer.echo(f"Pull request review context written to: {relative}")
    typer.echo(f"Line count: {len(path.read_text().splitlines())}")
    typer.echo("")
    typer.echo("You must read this file in full before reviewing the pull request.")
    typer.echo("You must report review findings to the user before proposing approval or merge.")
    typer.echo("Treat the pull request description as a review guide, not as proof that its claims are correct.")
    typer.echo("")
    typer.echo("Actions available after you have reported the review findings:")
    typer.echo(f"  python -B .agent_core/harness/main.py pr comment {pull_request.number} --file <markdown-file>")
    typer.echo(f"  python -B .agent_core/harness/main.py pr approve {pull_request.number} --file <markdown-file>")
    typer.echo(
        f"  python -B .agent_core/harness/main.py pr request-changes {pull_request.number} --file <markdown-file>"
    )
    typer.echo(f"  python -B .agent_core/harness/main.py pr merge {pull_request.number}")
    typer.echo("")
    typer.echo("Write substantive comments or reviews to a Markdown file, then use the applicable command above.")
    typer.echo("Do not approve, request changes, or merge until the user chooses that action.")
