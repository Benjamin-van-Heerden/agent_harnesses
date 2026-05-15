from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

from constants import GIT_USER_EMAIL, GIT_USER_NAME


HARNESS_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def run_command(
    args: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        args,
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        text=True,
        check=check,
    )


def command_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {"PYTHONDONTWRITEBYTECODE": "1"}
    if extra:
        env.update(extra)
    return env


def harness_command() -> list[str]:
    return [sys.executable, ".agent_core/harness/main.py"]


def install_harness(project_path: Path) -> None:
    run_command([str(HARNESS_ROOT / "setup.sh")], cwd=project_path)


def configure_git(project_path: Path) -> None:
    run_command(["git", "config", "user.name", GIT_USER_NAME], cwd=project_path)
    run_command(["git", "config", "user.email", GIT_USER_EMAIL], cwd=project_path)


def init_git_project(project_path: Path, branch: str = "main") -> None:
    run_command(["git", "init", "-b", branch], cwd=project_path)
    configure_git(project_path)
    run_command(["git", "commit", "--allow-empty", "-m", "initial commit"], cwd=project_path)
    for protected_branch in ("dev", "test"):
        if protected_branch != branch:
            run_command(["git", "branch", protected_branch], cwd=project_path)


def read_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data if isinstance(data, dict) else {}


def read_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            break
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip("'\"")
    return metadata


def markdown_body(path: Path) -> str:
    content = path.read_text()
    if not content.startswith("---\n"):
        return content
    _prefix, _separator, rest = content.partition("\n---\n")
    return rest


def write_legacy_state(
    project_path: Path,
    spec_issue_id: int | None = None,
    todo_issue_id: int | None = None,
) -> None:
    legacy_dir = project_path / ".mem"

    (legacy_dir / "specs" / "sample" / "tasks").mkdir(parents=True)
    (legacy_dir / "todos" / "claimed").mkdir(parents=True)
    (legacy_dir / "memories").mkdir(parents=True)
    (legacy_dir / "logs").mkdir(parents=True)
    (legacy_dir / "docs" / "core").mkdir(parents=True)
    (legacy_dir / "docs" / "guides").mkdir(parents=True)
    (legacy_dir / "docs" / "data").mkdir(parents=True)

    (legacy_dir / "config.toml").write_text(
        """
[project]
name = "Legacy Project"
description = "Legacy description"
generic_templates = ["python"]

[[files]]
path = "README.md"
description = "Readme"

[worktree]
symlink_paths = [".mem/docs/data", ".claude"]

[branches]
dev = "dev"
main = "prod"
test = "stage"
""".lstrip()
    )
    (legacy_dir / "user_mappings.toml").write_text("octo = \"Octo User\"\n")

    spec_issue_line = f"issue_id: {spec_issue_id}\n" if spec_issue_id is not None else ""
    todo_issue_line = f"issue_id: {todo_issue_id}\n" if todo_issue_id is not None else ""
    (legacy_dir / "specs" / "sample" / "spec.md").write_text(
        f"---\ntitle: Sample\nstatus: todo\n{spec_issue_line}---\nSample body\n"
    )
    (legacy_dir / "specs" / "sample" / "tasks" / "01_first.md").write_text(
        "---\ntitle: First\nstatus: todo\n---\nTask body\n"
    )
    (legacy_dir / "todos" / "open.md").write_text(
        f"---\ntitle: Open\nstatus: open\n{todo_issue_line}---\nTodo body\n"
    )
    (legacy_dir / "todos" / "claimed" / "done.md").write_text(
        "---\ntitle: Done\nstatus: claimed\n---\nDone body\n"
    )
    (legacy_dir / "memories" / "pattern.md").write_text(
        "---\ntitle: Pattern\n---\nMemory body\n"
    )
    (legacy_dir / "logs" / "user_20260513_120000_session.md").write_text(
        "---\ncreated_at: 2026-05-13T12:00:00\nusername: user\n---\nLog body\n"
    )
    (legacy_dir / "docs" / "alpha.md").write_text("Alpha docs\n")
    (legacy_dir / "docs" / "guides" / "gamma.md").write_text("Gamma docs\n")
    (legacy_dir / "docs" / "core" / "beta.md").write_text("Beta docs\n")
    (legacy_dir / "docs" / "data" / "index.bin").write_text("vector cache\n")
    (project_path / "AGENTS.md").write_text(
        "<MEMCONTENT>\nOld managed instructions\n</MEMCONTENT>\n\nUser notes\n"
    )
