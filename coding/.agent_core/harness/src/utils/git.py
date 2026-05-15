from __future__ import annotations

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


def fetch(cwd: Path | None = None) -> None:
    run_git(["fetch", "--prune"], cwd=cwd)


def pull_ff_only(branch: str, cwd: Path | None = None) -> None:
    run_git(["pull", "--ff-only", "origin", branch], cwd=cwd)


def checkout(branch: str, cwd: Path | None = None) -> None:
    run_git(["checkout", branch], cwd=cwd)


def protected_branch_sync(branches: BranchNames, cwd: Path | None = None) -> None:
    if has_uncommitted_changes(cwd):
        raise GitError("Working tree has uncommitted changes.")

    original = current_branch(cwd)
    fetch(cwd)
    for branch in branches.protected:
        checkout(branch, cwd)
        pull_ff_only(branch, cwd)
    if original:
        checkout(original, cwd)


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


def push_force_with_lease(branch: str, cwd: Path | None = None) -> None:
    run_git(["push", "--force-with-lease", "origin", branch], cwd=cwd)


def fetch_origin(cwd: Path | None = None) -> None:
    run_git(["fetch", "origin"], cwd=cwd)


def rebase_onto(remote_branch: str, cwd: Path | None = None) -> None:
    run_git(["rebase", remote_branch], cwd=cwd)
