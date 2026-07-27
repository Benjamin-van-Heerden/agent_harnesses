import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from github.GithubException import GithubException
from github.PullRequest import PullRequest
from github.Repository import Repository
from src.config.branches import get_branch_names
from src.config.paths import PROJECT_PATHS
from src.utils import git
from src.utils.errors import GitError, GitHubError
from src.utils.github import create_pull_request, delete_remote_branch, repository

PROMOTION_BRANCH_PREFIX = "promotion"
DESCRIPTION_PLACEHOLDER_PATTERN = re.compile(r"\{PROMOTION_DESCRIPTION:[^{}\n]+\}")
REQUIRED_DESCRIPTION_HEADINGS = (
    "## Executive summary",
    "## Included changes",
    "## Contributors and ownership",
    "## New functionality",
    "## Changed or removed behavior",
    "## Architecture and data flow",
    "## Important implementation details",
    "## Configuration, schema, and dependency changes",
    "## Testing and verification",
    "## Security and privacy considerations",
    "## Performance and operational impact",
    "## Compatibility and migration concerns",
    "## Risks",
    "## Deployment considerations",
    "## Rollback plan",
    "## Known limitations and follow-up work",
    "## Reviewer guide",
)


def _promotion_route(target: str) -> tuple[str, str]:
    branches = get_branch_names()
    logical_target = target.lower()
    if logical_target == "test":
        return branches.dev, branches.test
    if logical_target == "main":
        return branches.test, branches.main
    typer.echo(f"Invalid promotion target: {target}", err=True)
    typer.echo("Valid targets: test, main", err=True)
    raise typer.Exit(code=1)


def _description_path(target: str) -> Path:
    return PROJECT_PATHS.state_root / "tmp" / f"promotion_{target.lower()}.md"


def _description_template(source: str, target: str) -> str:
    return f"""# Promotion: {source} → {target}

## Executive summary

{{PROMOTION_DESCRIPTION: Explain what this promotion contains and why it is ready to move forward.}}

## Included changes

{{PROMOTION_DESCRIPTION: Describe the included specifications, fixes, and other changes.}}

## Contributors and ownership

{{PROMOTION_DESCRIPTION: Identify who made the changes and the areas they owned.}}

## New functionality

{{PROMOTION_DESCRIPTION: Explain newly introduced behavior and include focused code examples where they help reviewers.}}

## Changed or removed behavior

{{PROMOTION_DESCRIPTION: Explain behavior that changed or was removed, including compatibility implications.}}

## Architecture and data flow

{{PROMOTION_DESCRIPTION: Explain meaningful structural changes. Add a Mermaid diagram when it materially improves understanding.}}

## Important implementation details

{{PROMOTION_DESCRIPTION: Call out the files, modules, algorithms, and decisions reviewers should understand.}}

## Configuration, schema, and dependency changes

{{PROMOTION_DESCRIPTION: List configuration, database, environment, dependency, or infrastructure changes.}}

## Testing and verification

{{PROMOTION_DESCRIPTION: Record the tests and checks that were actually run and their outcomes.}}

## Security and privacy considerations

{{PROMOTION_DESCRIPTION: Describe relevant security, authorization, data handling, and privacy considerations.}}

## Performance and operational impact

{{PROMOTION_DESCRIPTION: Describe performance, observability, scaling, and operational effects.}}

## Compatibility and migration concerns

{{PROMOTION_DESCRIPTION: Describe migrations, rollout ordering, compatibility boundaries, and required operator actions.}}

## Risks

{{PROMOTION_DESCRIPTION: List concrete risks, their likelihood or impact where useful, and mitigations.}}

## Deployment considerations

{{PROMOTION_DESCRIPTION: Explain deployment sequencing, monitoring, and success criteria.}}

## Rollback plan

{{PROMOTION_DESCRIPTION: Explain how this promotion can be reversed or mitigated safely.}}

## Known limitations and follow-up work

{{PROMOTION_DESCRIPTION: List known limitations, deliberately excluded work, and follow-up items.}}

## Reviewer guide

{{PROMOTION_DESCRIPTION: Direct reviewers to the highest-risk changes and the most important files, snippets, tests, or diagrams.}}
"""


def _require_dev_checkout() -> None:
    branches = get_branch_names()
    current = git.current_branch()
    if current != branches.dev:
        typer.echo(
            f"Promotion creation must run from '{branches.dev}'. Current branch: {current or 'detached HEAD'}",
            err=True,
        )
        raise typer.Exit(code=1)
    if git.has_uncommitted_changes():
        typer.echo("Promotion creation requires a clean working tree.", err=True)
        raise typer.Exit(code=1)


def _require_source_checkout(source: str) -> None:
    current = git.current_branch()
    if current != source:
        typer.echo(
            f"Promotion execution must run from the inspected source branch '{source}'. Current branch: {current or 'detached HEAD'}",
            err=True,
        )
        raise typer.Exit(code=1)
    if git.has_uncommitted_changes():
        typer.echo("Promotion execution requires a clean working tree apart from the ignored description draft.", err=True)
        raise typer.Exit(code=1)


def _checkout_source(source: str) -> None:
    branches = get_branch_names()
    try:
        git.fetch()
        if source != branches.dev:
            git.checkout(source)
        git.pull_ff_only(source)
        if not git.same_commit(source, f"origin/{source}"):
            raise GitError(f"Local '{source}' does not match 'origin/{source}'.")
    except GitError as error:
        if git.current_branch() != branches.dev:
            try:
                git.checkout(branches.dev)
            except GitError:
                pass
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error


def _open_promotion_for_target(repo: Repository, target: str) -> PullRequest | None:
    try:
        for pull_request in repo.get_pulls(state="open", base=target):
            head = pull_request.head.ref
            if head.startswith(f"{PROMOTION_BRANCH_PREFIX}/{target}/"):
                return pull_request
    except GithubException as error:
        raise GitHubError(f"Could not inspect open promotions: {error}") from error
    return None


def _require_promotion_available(destination: str) -> None:
    try:
        repo = repository()
        existing = _open_promotion_for_target(repo, destination)
    except GitHubError as error:
        typer.echo("Promotion preparation requires working GitHub authentication.", err=True)
        typer.echo(str(error), err=True)
        typer.echo("Nothing was changed. Fix GitHub access, then run the preparation command again.", err=True)
        raise typer.Exit(code=1) from error
    if existing is not None:
        typer.echo(
            f"An open promotion already targets '{destination}': #{existing.number} {existing.title}",
            err=True,
        )
        typer.echo("Review, merge, or close that promotion before preparing another one.", err=True)
        raise typer.Exit(code=1)


def _prepare(target: str, source: str, destination: str) -> None:
    path = _description_path(target)
    if path.exists():
        typer.echo(f"Promotion description draft already exists: {path.relative_to(PROJECT_PATHS.project_root)}", err=True)
        typer.echo("Complete that draft or remove it deliberately before starting another promotion.", err=True)
        raise typer.Exit(code=1)
    _require_promotion_available(destination)
    _checkout_source(source)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_description_template(source, destination))
    relative = path.relative_to(PROJECT_PATHS.project_root)
    typer.echo("PROMOTION PREPARATION STARTED")
    typer.echo("")
    if source == get_branch_names().dev:
        typer.echo(f"You remain on '{source}', which has been synchronized with 'origin/{source}'.")
    else:
        typer.echo(f"You have been switched to '{source}', which has been synchronized with 'origin/{source}'.")
    typer.echo(f"You are preparing the promotion: {source} → {destination}")
    typer.echo(f"Promotion description draft: {relative}")
    typer.echo("")
    typer.echo("Nothing has been pushed. No snapshot branch or pull request has been created.")
    typer.echo("")
    typer.echo("WHAT YOU NEED TO DO")
    typer.echo("")
    typer.echo(f"1. Remain on '{source}' and treat all tracked files as read-only.")
    typer.echo(f"2. Inspect the complete change from 'origin/{destination}' to this '{source}' checkout.")
    typer.echo("3. Run the checks needed to support the description and record only verified results.")
    typer.echo(f"4. Fill in '{relative}', replacing every {{PROMOTION_DESCRIPTION: ...}} placeholder.")
    typer.echo("5. Make the description detailed enough to guide both human and agent reviewers. Use focused code snippets and Mermaid diagrams when useful.")
    typer.echo("")
    typer.echo("When that work is complete, run this command without switching branches:")
    typer.echo(
        f"  python -B .agent_core/harness/main.py promotion create {target.lower()} --execute"
    )
    typer.echo("")
    typer.echo("That command will validate the description, create a remote-only snapshot from the code you inspected, open the pull request, remove the temporary draft, and switch you back to the development branch.")


def _execute(target: str, source: str, destination: str) -> None:
    description_path = _description_path(target)
    if not description_path.is_file():
        typer.echo(f"Missing promotion description draft: {description_path.relative_to(PROJECT_PATHS.project_root)}", err=True)
        typer.echo(
            f"Run `python -B .agent_core/harness/main.py promotion create {target.lower()}` first.",
            err=True,
        )
        raise typer.Exit(code=1)
    description = description_path.read_text().strip()
    placeholders = DESCRIPTION_PLACEHOLDER_PATTERN.findall(description)
    if placeholders:
        typer.echo("Promotion description draft still contains placeholders:", err=True)
        for placeholder in placeholders:
            typer.echo(f"  - {placeholder}", err=True)
        raise typer.Exit(code=1)
    missing_headings = [
        heading for heading in REQUIRED_DESCRIPTION_HEADINGS if heading not in description
    ]
    if missing_headings:
        typer.echo("Promotion description draft is missing required sections:", err=True)
        for heading in missing_headings:
            typer.echo(f"  - {heading}", err=True)
        raise typer.Exit(code=1)

    typer.echo("PROMOTION DESCRIPTION VALIDATED")
    typer.echo("")
    typer.echo(f"Source checkout: {source}")
    typer.echo(f"Destination: {destination}")
    typer.echo("")
    typer.echo("The harness will now create a remote-only snapshot branch from this source checkout, open the promotion pull request with the completed description, remove the temporary draft, and switch back to the development branch.")
    typer.echo(f"The destination branch '{destination}' will not be advanced by this command.")
    typer.echo("")

    repo: Repository | None = None
    branch: str | None = None
    try:
        git.fetch()
        source_ref = source
        destination_ref = f"origin/{destination}"
        if not git.is_ancestor(destination_ref, source_ref):
            raise GitError(
                f"Cannot promote '{source}' into '{destination}' with a fast-forward. "
                f"origin/{destination} is not an ancestor of the inspected local '{source}' branch."
            )
        if git.same_commit(source_ref, destination_ref):
            raise GitError(f"No changes are available to promote from '{source}' into '{destination}'.")

        repo = repository()
        existing = _open_promotion_for_target(repo, destination)
        if existing is not None:
            typer.echo(
                f"An open promotion already targets '{destination}': #{existing.number} {existing.title}",
                err=True,
            )
            raise typer.Exit(code=1)

        branch = f"{PROMOTION_BRANCH_PREFIX}/{destination}/{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        git.push_ref(source_ref, branch)
        title = f"[Promote]: {source} → {destination}"
        pull_request = create_pull_request(repo, title, description, branch, destination)
    except typer.Exit:
        raise
    except (GitError, GitHubError) as error:
        if repo is not None and branch is not None:
            try:
                delete_remote_branch(repo, branch)
            except GitHubError:
                pass
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    try:
        description_path.unlink()
    except OSError as error:
        typer.echo(f"Warning: could not remove temporary promotion description draft: {error}", err=True)
    branches = get_branch_names()
    try:
        git.checkout(branches.dev)
    except GitError as error:
        typer.echo(f"Warning: promotion PR was created, but the harness could not return to '{branches.dev}': {error}", err=True)
    typer.echo(f"Promotion pull request: {pull_request.html_url}")
    typer.echo(f"Remote snapshot branch: {branch}")
    if git.current_branch() == branches.dev:
        typer.echo(f"You have been switched back to '{branches.dev}' mission control.")
    typer.echo("")
    typer.echo("To begin the review workflow, run:")
    typer.echo(f"  python -B .agent_core/harness/main.py pr review {pull_request.number}")


def _direct_confirmation(target: str, source: str, destination: str) -> None:
    target_label = "production" if target.lower() == "main" else destination
    typer.echo("DIRECT PROMOTION CONFIRMATION REQUIRED", err=True)
    typer.echo("", err=True)
    typer.echo(f"Route: {source} → {destination}", err=True)
    typer.echo("", err=True)
    typer.echo("This bypasses the promotion description, snapshot branch, pull request, review, and pull-request checks.", err=True)
    typer.echo(
        f'You must ask the user: "Are you sure you want to promote {source} directly into {target_label} without a pull request?"',
        err=True,
    )
    typer.echo("Do not proceed until the user explicitly confirms.", err=True)
    typer.echo("", err=True)
    typer.echo("After confirmation, run the command printed below:", err=True)
    typer.echo(
        f"  python -B .agent_core/harness/main.py promotion create {target.lower()} --no-pr --force",
        err=True,
    )
    raise typer.Exit(code=1)


def _promote_directly(source: str, destination: str) -> None:
    try:
        git.fetch()
        source_ref = f"origin/{source}"
        destination_ref = f"origin/{destination}"
        if not git.is_ancestor(destination_ref, source_ref):
            raise GitError(
                f"Cannot promote '{source}' directly into '{destination}' with a fast-forward. "
                f"origin/{destination} is not an ancestor of origin/{source}."
            )
        if git.same_commit(source_ref, destination_ref):
            raise GitError(f"No changes are available to promote from '{source}' into '{destination}'.")

        repo = repository()
        existing = _open_promotion_for_target(repo, destination)
        if existing is not None:
            typer.echo(
                f"An open promotion already targets '{destination}': #{existing.number} {existing.title}",
                err=True,
            )
            typer.echo("Review, merge, or close that promotion before attempting a direct promotion.", err=True)
            raise typer.Exit(code=1)
        git.push_ref(source_ref, destination)
    except typer.Exit:
        raise
    except (GitError, GitHubError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Fast-forwarded '{destination}' directly to 'origin/{source}'.")
    typer.echo("No promotion description, snapshot branch, or pull request was created.")


def run(
    target: Annotated[str, typer.Argument(help="Logical promotion target: test or main")],
    execute: Annotated[
        bool,
        typer.Option(
            "--execute",
            help="Create the remote snapshot branch and pull request from a completed promotion description.",
        ),
    ] = False,
    no_pr: Annotated[
        bool,
        typer.Option(
            "--no-pr",
            help="Request a direct fast-forward promotion without a pull request.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Proceed after the direct-promotion confirmation.",
            hidden=True,
        ),
    ] = False,
) -> None:
    source, destination = _promotion_route(target)
    if execute and no_pr:
        typer.echo("--execute and --no-pr cannot be used together.", err=True)
        raise typer.Exit(code=1)
    if force and not no_pr:
        typer.echo("--force is only valid with --no-pr.", err=True)
        raise typer.Exit(code=1)
    if no_pr:
        _require_dev_checkout()
        if not force:
            _direct_confirmation(target, source, destination)
        _promote_directly(source, destination)
        return
    if execute:
        _require_source_checkout(source)
        _execute(target, source, destination)
        return
    _require_dev_checkout()
    _prepare(target, source, destination)
