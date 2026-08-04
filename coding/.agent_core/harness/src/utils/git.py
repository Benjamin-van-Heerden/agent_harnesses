import subprocess
from pathlib import Path

from src.config.models import BranchNames
from src.config.paths import PROJECT_PATHS
from src.utils.errors import GitError


def run_git(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or PROJECT_PATHS.project_root,
            check=check,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or str(error)
        raise GitError(message) from error


def current_branch(cwd: Path | None = None) -> str | None:
    result = run_git(["branch", "--show-current"], cwd=cwd, check=False)
    branch = result.stdout.strip()
    return branch or None


def has_uncommitted_changes(cwd: Path | None = None) -> bool:
    result = run_git(["status", "--porcelain"], cwd=cwd, check=False)
    return bool(result.stdout.strip())


def has_tracked_changes(cwd: Path | None = None) -> bool:
    result = run_git(["status", "--porcelain", "--untracked-files=no"], cwd=cwd, check=False)
    return bool(result.stdout.strip())


def fetch(cwd: Path | None = None) -> None:
    run_git(["fetch", "--prune"], cwd=cwd)


def pull_ff_only(branch: str, cwd: Path | None = None) -> None:
    run_git(["pull", "--ff-only", "origin", branch], cwd=cwd)


def merge_ff_only(branch: str, cwd: Path | None = None) -> None:
    run_git(["merge", "--ff-only", branch], cwd=cwd)


def is_ancestor(ancestor: str, descendant: str, cwd: Path | None = None) -> bool:
    result = run_git(["merge-base", "--is-ancestor", ancestor, descendant], cwd=cwd, check=False)
    return result.returncode == 0


def same_commit(first: str, second: str, cwd: Path | None = None) -> bool:
    first_result = run_git(["rev-parse", first], cwd=cwd)
    second_result = run_git(["rev-parse", second], cwd=cwd)
    return first_result.stdout.strip() == second_result.stdout.strip()


def rev_parse(ref: str, cwd: Path | None = None) -> str:
    return run_git(["rev-parse", ref], cwd=cwd).stdout.strip()


def commit_subject(ref: str, cwd: Path | None = None) -> str:
    return run_git(["log", "-1", "--format=%s", ref], cwd=cwd).stdout.strip()


def parent_count(ref: str, cwd: Path | None = None) -> int:
    result = run_git(["log", "-1", "--format=%P", ref], cwd=cwd, check=False)
    if result.returncode != 0:
        return 0
    parents = result.stdout.strip().split()
    return len(parents)


def is_merge_commit(ref: str, cwd: Path | None = None) -> bool:
    return parent_count(ref, cwd=cwd) >= 2


def commits_reachable_from(included: str, excluded: str, cwd: Path | None = None) -> list[str]:
    result = run_git(
        ["rev-list", "--reverse", f"{excluded}..{included}"],
        cwd=cwd,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"Could not list commits for {excluded}..{included}."
        raise GitError(message)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def commit_onelines(included: str, excluded: str, cwd: Path | None = None) -> list[str]:
    result = run_git(
        ["log", "--oneline", "--no-decorate", f"{excluded}..{included}"],
        cwd=cwd,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"Could not log commits for {excluded}..{included}."
        raise GitError(message)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def checkout(branch: str, cwd: Path | None = None) -> None:
    run_git(["checkout", branch], cwd=cwd)


def checkout_new_branch(branch: str, start_point: str, cwd: Path | None = None) -> None:
    run_git(["checkout", "-B", branch, start_point], cwd=cwd)


def merge_no_ff(revision: str, message: str, cwd: Path | None = None) -> None:
    run_git(["merge", "--no-ff", "-m", message, revision], cwd=cwd)


def merge_abort(cwd: Path | None = None) -> None:
    run_git(["merge", "--abort"], cwd=cwd, check=False)


def local_branch_exists(branch: str, cwd: Path | None = None) -> bool:
    result = run_git(["show-ref", "--verify", f"refs/heads/{branch}"], cwd=cwd, check=False)
    return result.returncode == 0


def remote_branch_exists(branch: str, cwd: Path | None = None) -> bool:
    result = run_git(
        ["show-ref", "--verify", f"refs/remotes/origin/{branch}"],
        cwd=cwd,
        check=False,
    )
    return result.returncode == 0


def local_ahead_of_remote(branch: str, cwd: Path | None = None) -> bool:
    result = run_git(
        ["rev-list", "--count", f"origin/{branch}..{branch}"],
        cwd=cwd,
        check=False,
    )
    try:
        return result.returncode == 0 and int(result.stdout.strip()) > 0
    except ValueError:
        return False


def remote_ahead_of_local(branch: str, cwd: Path | None = None) -> bool:
    result = run_git(
        ["rev-list", "--count", f"{branch}..origin/{branch}"],
        cwd=cwd,
        check=False,
    )
    try:
        return result.returncode == 0 and int(result.stdout.strip()) > 0
    except ValueError:
        return False


def assert_protected_branches_available(branches: BranchNames, cwd: Path | None = None) -> None:
    missing: list[str] = []
    for branch in branches.protected:
        if not local_branch_exists(branch, cwd):
            missing.append(f"{branch} (local)")
        if not remote_branch_exists(branch, cwd):
            missing.append(f"origin/{branch}")
    if missing:
        joined = ", ".join(missing)
        raise GitError(f"Required protected branch(es) missing: {joined}")


def protected_branch_sync(branches: BranchNames, cwd: Path | None = None) -> None:
    if has_tracked_changes(cwd):
        raise GitError("Working tree has uncommitted tracked changes.")

    current = current_branch(cwd)
    fetch(cwd)
    assert_protected_branches_available(branches, cwd)
    for branch in branches.protected:
        if branch == current:
            if local_ahead_of_remote(branch, cwd):
                rebase_onto(f"origin/{branch}", cwd)
            elif remote_ahead_of_local(branch, cwd):
                run_git(["merge", "--ff-only", f"origin/{branch}"], cwd=cwd)
            continue

        if local_ahead_of_remote(branch, cwd):
            raise GitError(
                f"Protected branch '{branch}' has local commits that are not on origin/{branch}. "
                "Onboard will not checkout or mutate non-current protected branches. "
                f"You must inspect and sync '{branch}' deliberately."
            )


def sync_current_branch(branches: BranchNames, cwd: Path | None = None) -> None:
    branch = current_branch(cwd)
    if branch is None:
        raise GitError("Could not determine current branch.")
    if has_tracked_changes(cwd):
        raise GitError("Working tree has uncommitted tracked changes.")

    fetch(cwd)
    assert_protected_branches_available(branches, cwd)

    parent = branches.noswitch_branches.parent_for(branch)
    if parent is not None:
        if not remote_branch_exists(parent, cwd):
            raise GitError(f"Configured parent branch does not exist on origin: {parent}")
        rebase_onto(f"origin/{parent}", cwd)
        return

    if branch.startswith(f"{branches.dev}-"):
        rebase_onto(f"origin/{branches.dev}", cwd)
        push_force_with_lease(branch, cwd)
        return

    if branch in branches.protected:
        protected_branch_sync(branches, cwd)
        return

    pull_ff_only(branch, cwd)


def delete_local_branch(branch: str, force: bool = False, cwd: Path | None = None) -> None:
    flag = "-D" if force else "-d"
    run_git(["branch", flag, branch], cwd=cwd)


def prune(cwd: Path | None = None) -> None:
    run_git(["remote", "prune", "origin"], cwd=cwd)


def add_all(cwd: Path | None = None) -> None:
    run_git(["add", "-A"], cwd=cwd)


def commit(message: str, cwd: Path | None = None) -> bool:
    result = run_git(["diff", "--cached", "--quiet"], cwd=cwd, check=False)
    if result.returncode == 0:
        return False
    run_git(["commit", "-m", message], cwd=cwd)
    return True


def push(branch: str | None = None, cwd: Path | None = None, set_upstream: bool = False) -> None:
    args = ["push"]
    if set_upstream:
        args.extend(["--set-upstream", "origin", branch or current_branch(cwd) or "HEAD"])
    elif branch:
        args.extend(["origin", branch])
    run_git(args, cwd=cwd)


def push_ref(source: str, branch: str, cwd: Path | None = None) -> None:
    run_git(["push", "origin", f"{source}:refs/heads/{branch}"], cwd=cwd)


def update_local_branch(branch: str, revision: str, cwd: Path | None = None) -> None:
    run_git(["branch", "--force", branch, revision], cwd=cwd)


def push_force_with_lease(branch: str, cwd: Path | None = None) -> None:
    run_git(["push", "--force-with-lease", "origin", branch], cwd=cwd)


def fetch_origin(cwd: Path | None = None) -> None:
    run_git(["fetch", "origin"], cwd=cwd)


def rebase_onto(remote_branch: str, cwd: Path | None = None) -> None:
    run_git(["rebase", remote_branch], cwd=cwd)
