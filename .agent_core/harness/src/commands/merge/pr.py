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
        typer.Argument(help="PR URL to merge. PR number or spec slug are also accepted."),
    ] = None,
    message: Annotated[
        str | None,
        typer.Option(
            "--message", "-m", help="Commit message for the pull request merge"
        ),
    ] = None,
) -> None:
    branches = get_branch_names()
    require_clean_worktree()
    require_current_branch(branches.dev)
    if pr_ref is None:
        list_pull_requests(branches.dev)
        return

    merge_pull_request_into_base(pr_ref, branches.dev, message)
