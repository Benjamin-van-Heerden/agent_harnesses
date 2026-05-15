"""Usage: git_snapshot.py [message]

Stage all non-ignored project files and create a local git commit if anything
changed. No push is performed; Praxis repositories are local snapshots inside
cloud-synced folders.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from _lib import die, praxis_root

DEFAULT_MESSAGE = "Praxis onboard snapshot"


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    root = praxis_root()
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        die("usage: git_snapshot.py [message]")
    if shutil.which("git") is None:
        die("git is not installed or not on PATH")

    message = argv[0] if argv else DEFAULT_MESSAGE
    root = praxis_root()
    if not (root / ".git").is_dir():
        die("git repository not initialised; rerun praxis setup or update")

    run_git(["add", "-A"])

    diff = run_git(["diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        print("praxis: git snapshot: nothing to commit")
        return
    if diff.returncode != 1:
        stderr = diff.stderr.strip() or "unknown git diff error"
        die(f"git diff failed: {stderr}")

    commit = run_git(
        [
            "-c",
            "user.name=Praxis",
            "-c",
            "user.email=praxis@local",
            "commit",
            "-m",
            message,
        ],
        check=False,
    )
    if commit.returncode != 0:
        stderr = commit.stderr.strip() or commit.stdout.strip() or "unknown git commit error"
        die(f"git commit failed: {stderr}")

    summary = commit.stdout.strip().splitlines()[0]
    print(f"praxis: git snapshot: {summary}")


if __name__ == "__main__":
    main(sys.argv[1:])
