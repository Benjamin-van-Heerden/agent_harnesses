import typer

from src.config.branches import get_branch_names
from src.config.models import BranchNames
from src.utils import git
from src.utils.errors import GitError


class OnboardBlockedError(Exception):
    pass


def sync_warning_from_exit(error: typer.Exit) -> str:
    cause = error.__cause__
    if cause is not None:
        return str(cause)
    return f"Sync failed with exit code {error.exit_code}."


def _sync_target_branch(branch: str, branches: BranchNames) -> str:
    parent = branches.noswitch_branches.parent_for(branch)
    if parent is not None:
        return parent
    if branch.startswith(f"{branches.dev}-"):
        return branches.dev
    return branch


def _commit_count(revision_range: str) -> int | None:
    result = git.run_git(["rev-list", "--count", revision_range], check=False)
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def _remote_status_summary(branch: str, branches: BranchNames) -> str:
    target = _sync_target_branch(branch, branches)
    remote_ref = f"origin/{target}"
    if not git.remote_branch_exists(target):
        return f"Remote check: `{remote_ref}` does not exist."

    remote_only = _commit_count(f"HEAD..{remote_ref}")
    local_only = _commit_count(f"{remote_ref}..HEAD")
    if remote_only is None or local_only is None:
        return f"Remote check: could not compare `HEAD` with `{remote_ref}`."

    if target != branch:
        return (
            f"Remote check: current branch `{branch}` syncs against `{remote_ref}`; "
            f"{remote_only} remote commit(s) and {local_only} local commit(s) differ."
        )
    if remote_only and local_only:
        return (
            f"Remote check: `{branch}` has diverged from `{remote_ref}` "
            f"({local_only} local commit(s), {remote_only} remote commit(s))."
        )
    if remote_only:
        return (
            f"Remote check: `{branch}` is behind `{remote_ref}` by "
            f"{remote_only} commit(s)."
        )
    if local_only:
        return (
            f"Remote check: `{branch}` is ahead of `{remote_ref}` by "
            f"{local_only} commit(s)."
        )
    return f"Remote check: `{branch}` is up to date with `{remote_ref}`."


def _status_lines(max_lines: int = 20) -> list[str]:
    result = git.run_git(["status", "--short"], check=False)
    lines = result.stdout.splitlines()
    if len(lines) <= max_lines:
        return lines
    return [*lines[:max_lines], f"... {len(lines) - max_lines} more file(s)"]


def _dirty_worktree_message(continue_requested: bool) -> str:
    branch = git.current_branch() or "detached HEAD"
    try:
        remote_status = _remote_status_summary(branch, get_branch_names())
    except (GitError, ValueError) as error:
        remote_status = f"Remote check failed after fetch: {error}"

    lines = ["Onboard stopped before building project context."]
    if continue_requested:
        lines.append("`--continue` was requested, but the working tree is still dirty.")
    lines.append(remote_status)
    lines.append("The working tree has uncommitted changes:")
    for line in _status_lines():
        lines.append(f"  {line}")
    lines.extend(
        [
            "",
            "You must resolve these changes before onboarding can continue.",
            "Commit, stash, or discard the local changes, then run:",
            "  python -B .agent_core/harness/main.py onboard --continue",
            "",
            "No onboard context file was created because local context may be stale.",
        ]
    )
    return "\n".join(lines)


def run_git_preflight(continue_requested: bool) -> None:
    try:
        git.fetch()
    except GitError as error:
        raise OnboardBlockedError(
            "\n".join(
                [
                    "Onboard stopped before building project context.",
                    f"Remote fetch failed: {error}",
                    "",
                    "You must resolve git connectivity or remote configuration before onboarding can continue.",
                    "Then run:",
                    "  python -B .agent_core/harness/main.py onboard --continue",
                    "",
                    "No onboard context file was created because remote context could not be verified.",
                ]
            )
        ) from error

    if git.has_uncommitted_changes():
        raise OnboardBlockedError(_dirty_worktree_message(continue_requested))
