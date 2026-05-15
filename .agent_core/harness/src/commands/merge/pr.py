from typing import Annotated

import typer

from src.commands.merge.utils import (
    list_pull_requests,
    merge_pull_request_into_base,
    require_clean_worktree,
    require_current_branch,
)
from src.config.branches import get_branch_names


def run(
    pr_ref: Annotated[
        str | None,
        typer.Argument(help="PR number, PR URL, or spec slug to merge"),
    ] = None,
    message: Annotated[
        str | None,
        typer.Option("--message", "-m", help="Commit message for the pull request merge"),
    ] = None,
) -> None:
    branches = get_branch_names()
    if pr_ref is None:
        list_pull_requests(branches.dev)
        return

    require_clean_worktree()
    require_current_branch(branches.dev)
    merge_pull_request_into_base(pr_ref, branches.dev, message)
