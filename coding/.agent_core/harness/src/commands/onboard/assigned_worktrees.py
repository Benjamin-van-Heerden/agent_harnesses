from dataclasses import dataclass
from pathlib import Path

from src.state import specs
from src.state.models import Spec
from src.utils import git, worktrees
from src.utils.errors import GitError
from src.utils.github import authenticated_username


@dataclass(frozen=True)
class AssignedWorktreeResult:
    spec_slug: str
    branch: str
    path: Path


def _is_active_assigned_spec(record: Spec, username: str) -> bool:
    return (
        record.status in {"todo", "merge_ready"}
        and record.assigned_to == username
        and record.branch is not None
    )


def _has_local_worktree(record: Spec) -> bool:
    expected_path = worktrees.path_for(record.slug)
    for item in worktrees.list_all():
        if item.path == expected_path or item.branch == record.branch:
            return True
    return False


def create_missing_for_authenticated_user() -> list[AssignedWorktreeResult]:
    if worktrees.is_worktree():
        return []

    username = authenticated_username()
    candidates = [
        record
        for record in specs.list_all()
        if _is_active_assigned_spec(record, username) and not _has_local_worktree(record)
    ]
    if not candidates:
        return []

    git.fetch()
    created: list[AssignedWorktreeResult] = []
    for record in candidates:
        branch = record.branch
        if branch is None:
            continue
        if not git.remote_branch_exists(branch):
            raise GitError(
                f"Spec '{record.slug}' is assigned to you, but the remote branch is missing: origin/{branch}\n"
                f"The assigning user must push the assigned branch, or repair the branch recorded in the spec before onboarding can create the worktree."
            )
        path = worktrees.create_from_remote(record.slug, branch)
        created.append(AssignedWorktreeResult(spec_slug=record.slug, branch=branch, path=path))
    return created
