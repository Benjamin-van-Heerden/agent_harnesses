import subprocess
from datetime import datetime
from pathlib import Path


def run_git(project_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def post_command_snapshot(project_root: Path) -> None:
    if run_git(project_root, ["rev-parse", "--git-dir"]).returncode != 0:
        return

    status = run_git(project_root, ["status", "--porcelain"])
    if status.returncode != 0 or not status.stdout.strip():
        return

    add = run_git(project_root, ["add", "-A"])
    if add.returncode != 0:
        print("Git snapshot skipped: failed to stage changes.")
        return

    message = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit = run_git(project_root, ["commit", "-m", message])
    if commit.returncode != 0:
        print("Git snapshot skipped: failed to create a local commit.")
        return

    print(f"Created local git snapshot: {message}")
