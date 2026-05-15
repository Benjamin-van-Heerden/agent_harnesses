from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from src.config.paths import PROJECT_PATHS
from src.utils.git import run_git


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str
    is_main: bool


def is_worktree(path: Path | None = None) -> bool:
    return ((path or PROJECT_PATHS.project_root) / ".git").is_file()


def base_dir(main_repo_path: Path | None = None) -> Path:
    root = (main_repo_path or PROJECT_PATHS.project_root).resolve()
    return root.parent / f"{root.name}-worktrees"


def path_for(slug: str, main_repo_path: Path | None = None) -> Path:
    return base_dir(main_repo_path) / slug


def list_all(main_repo_path: Path | None = None) -> list[WorktreeInfo]:
    root = main_repo_path or PROJECT_PATHS.project_root
    result = run_git(["worktree", "list", "--porcelain"], cwd=root)
    records: list[WorktreeInfo] = []
    current_path: Path | None = None
    current_branch = ""

    for line in result.stdout.splitlines() + [""]:
        if line.startswith("worktree "):
            current_path = Path(line.split(" ", 1)[1])
            current_branch = ""
        elif line.startswith("branch "):
            current_branch = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line == "" and current_path is not None:
            records.append(
                WorktreeInfo(
                    path=current_path,
                    branch=current_branch,
                    is_main=current_path.resolve() == root.resolve(),
                )
            )
            current_path = None

    return records


def create(slug: str, branch: str, main_repo_path: Path | None = None) -> Path:
    root = main_repo_path or PROJECT_PATHS.project_root
    target = path_for(slug, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    result = run_git(["branch", "--list", branch], cwd=root, check=False)
    if result.stdout.strip():
        run_git(["worktree", "add", str(target), branch], cwd=root)
    else:
        run_git(["worktree", "add", "-b", branch, str(target)], cwd=root)
    return target


def remove(slug: str, force: bool = False, main_repo_path: Path | None = None) -> bool:
    root = main_repo_path or PROJECT_PATHS.project_root
    target = path_for(slug, root)
    if not target.exists():
        return False
    args = ["worktree", "remove", str(target)]
    if force:
        args.append("--force")
    result = run_git(args, cwd=root, check=False)
    if result.returncode != 0 and target.exists():
        shutil.rmtree(target, ignore_errors=True)
    run_git(["worktree", "prune"], cwd=root, check=False)
    return True
