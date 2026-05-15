from typing import Annotated

import typer

from src.commands.merge.utils import (
    list_pull_requests,
    merge_pull_request_into_base,
    promote_branch,
    require_clean_worktree,
    require_current_branch,
)
from src.config.branches import get_branch_names


def run(
    target: Annotated[
        str,
        typer.Argument(help="Logical target branch: test or main"),
    ],
    source: Annotated[
        str | None,
        typer.Argument(help="Source: dev, test, or pr"),
    ] = None,
    pr_ref: Annotated[
        str | None,
        typer.Argument(help="PR number, PR URL, or spec slug when source is pr"),
    ] = None,
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Commit message for a pull request merge"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Required for merges into the logical main branch"),
    ] = False,
) -> None:
    branches = get_branch_names()
    logical_target = target.lower()
    logical_source = source.lower() if source is not None else None

    if logical_target == "test":
        if logical_source == "dev":
            promote_branch(branches.dev, branches.test)
            return
        if logical_source == "pr":
            if pr_ref is None:
                list_pull_requests(branches.test)
                return
            require_clean_worktree()
            require_current_branch(branches.test)
            merge_pull_request_into_base(pr_ref, branches.test, message)
            return
        _invalid_merge_into(target, source)

    if logical_target == "main":
        if logical_source == "pr" and pr_ref is None:
            list_pull_requests(branches.main)
            return
        if not force:
            typer.echo("Merges into the logical main branch require --force.", err=True)
            raise typer.Exit(code=1)
        if logical_source == "test":
            promote_branch(branches.test, branches.main)
            return
        if logical_source == "pr":
            require_clean_worktree()
            require_current_branch(branches.main)
            merge_pull_request_into_base(pr_ref or "", branches.main, message)
            return
        _invalid_merge_into(target, source)

    _invalid_merge_into(target, source)


def _invalid_merge_into(target: str, source: str | None) -> None:
    typed = f"{target} {source}" if source is not None else target
    typer.echo(f"Invalid merge target/source: {typed}", err=True)
    typer.echo("Valid forms:", err=True)
    typer.echo("  merge into test dev", err=True)
    typer.echo("  merge into test pr [pr_ref]", err=True)
    typer.echo("  merge into main test --force", err=True)
    typer.echo("  merge into main pr [pr_ref] --force", err=True)
    raise typer.Exit(code=1)
