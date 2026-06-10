#!/usr/bin/env python3
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn, cast


REPO_ARCHIVE_URL = "https://github.com/Benjamin-van-Heerden/agent_harnesses/archive/refs/heads/main.zip"
TEMPLATE_SUBPATH = "coding"
CORE_START_TAG = "<core_instructions>"
CORE_END_TAG = "</core_instructions>"
LEGACY_CORE_START_TAG = "<AGENT_CORE>"
LEGACY_CORE_END_TAG = "</AGENT_CORE>"
DEFAULT_DOCS = ("coding_general", "coding_testing")
WORKTREE_SYMLINK_PATHS_COMMENT = (
    "# Project-root relative paths to symlink from the main checkout into spec worktrees.",
    "# Every listed path is automatically added to .gitignore and must be safe to keep untracked.",
    "# Typical examples are .env, .claude, .venv, node_modules, or deps. Use care with manifests and lock files such as pyproject.toml, package.json, or bun.lock; list them only when the project deliberately treats them as local-only.",
)
OPTIONAL_ONBOARD_CONFIG_BLOCKS = {
    "files": "\n".join(
        (
            "# Files to include in onboard output",
            "# [[files]]",
            '# path = "README.md"',
            '# description = "Project overview and setup instructions"',
        )
    ),
    "tree_dirs": "\n".join(
        (
            "# Directories whose tree structure is included in onboard output",
            "# [[tree_dirs]]",
            '# path = "src"',
            '# description = "Source code"',
        )
    ),
    "runnables": "\n".join(
        (
            "# Commands whose output is included in onboard output",
            "# [[runnables]]",
            '# name = "Generated project context"',
            '# command = "python -m your_tool --print-context"',
            '# description = "Generated project context"',
            "# timeout_seconds = 60",
        )
    ),
}
LEGACY_WORKTREE_SYMLINK_PATHS_COMMENT = "# Paths to symlink into worktrees instead of copying"
AGENT_CORE_TMP_IGNORE_ENTRY = ".agent_core/tmp/"
LEGACY_AGENT_CORE_TMP_IGNORE_ENTRY = ".agent_core/tmp"
INSTALL_COMMIT_MESSAGE = "install agent harness"
UNINSTALL_COMMIT_MESSAGE = "uninstall agent harness"
UNINSTALL_CONFIRMATION = "I am sure"
HARNESS_GITHUB_LABELS = (
    "spec",
    "todo",
    "status:todo",
    "status:merge-ready",
    "status:completed",
    "status:abandoned",
)
HARNESS_MANAGED_PATHS = (".agent_core", "AGENTS.md", "CLAUDE.md", ".gitignore")


@dataclass(frozen=True)
class ConfigKeyCommentPatch:
    section: str
    key: str
    comment_lines: tuple[str, ...]
    legacy_comment_blocks: tuple[tuple[str, ...], ...] = ()


CONFIG_PATCHES = (
    ConfigKeyCommentPatch(
        section="worktree",
        key="symlink_paths",
        comment_lines=WORKTREE_SYMLINK_PATHS_COMMENT,
        legacy_comment_blocks=((LEGACY_WORKTREE_SYMLINK_PATHS_COMMENT,),),
    ),
)


class SetupError(Exception):
    pass


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def fail(message: str) -> NoReturn:
    raise SetupError(message)


def normalize_argv(argv: list[str]) -> list[str]:
    if argv and argv[0] == "--":
        return argv[1:]
    return argv


def usage() -> str:
    return """Usage:
  setup.py [--update]
  setup.py --uninstall
  setup.py docs list
  setup.py docs add <slug> [slug ...]
  setup.py docs update [slug ...]

Docs commands copy optional docs into .agent_core/docs/.
When docs update is run without slugs, it updates installed docs that still
match a document in the harness optional_docs directory.
"""


def resolve_template_root() -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    script_file = globals().get("__file__")
    if script_file:
        script_dir = Path(script_file).resolve().parent
        if (script_dir / ".agent_core" / "harness").is_dir():
            return script_dir, None

    temp_dir = tempfile.TemporaryDirectory(prefix="agent-harnesses-setup-")
    eprint("Fetching latest agent harness templates...")
    with urllib.request.urlopen(REPO_ARCHIVE_URL) as response:
        archive = response.read()

    with zipfile.ZipFile(io.BytesIO(archive)) as repo_zip:
        repo_zip.extractall(temp_dir.name)

    root = Path(temp_dir.name)
    for candidate in root.iterdir():
        template_root = candidate / TEMPLATE_SUBPATH
        if (template_root / ".agent_core" / "harness").is_dir():
            return template_root, temp_dir

    temp_dir.cleanup()
    fail(f"Error: template subdirectory '{TEMPLATE_SUBPATH}' not found in repository archive.")


def run_git(target_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(target_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        fail(message)
    return result


def git_stdout(target_root: Path, args: list[str]) -> str:
    return run_git(target_root, args).stdout.strip()


def current_branch(target_root: Path) -> str:
    branch = git_stdout(target_root, ["branch", "--show-current"])
    if not branch:
        fail("Error: setup must run on a named branch, not detached HEAD.")
    return branch


def ensure_git_repository(target_root: Path) -> None:
    if shutil.which("git") is None:
        fail("Error: git is required but was not found on PATH.")
    if run_git(target_root, ["rev-parse", "--git-dir"], check=False).returncode != 0:
        fail("Error: setup must be run from an initialized git repository.")
    if run_git(target_root, ["rev-parse", "--verify", "HEAD"], check=False).returncode != 0:
        fail("Error: setup requires at least one commit before protected branches can be managed.")


def status_lines(target_root: Path) -> list[str]:
    output = git_stdout(target_root, ["status", "--porcelain"])
    return [line for line in output.splitlines() if line]


def ensure_clean_worktree(target_root: Path, action: str) -> None:
    lines = status_lines(target_root)
    if not lines:
        return
    eprint(f"Error: cannot {action} with a dirty working tree.")
    eprint("Resolve these changes before running setup:")
    for line in lines:
        eprint(f"  {line}")
    raise SetupError("Working tree is dirty.")


def default_config(project_name: str) -> str:
    return f'''[project]
name = "{project_name}"
description = """
Add your project description here.
"""

# Files to include in onboard output
# [[files]]
# path = "README.md"
# description = "Project overview and setup instructions"

# Directories whose tree structure is included in onboard output
# [[tree_dirs]]
# path = "src"
# description = "Source code"

# Commands whose output is included in onboard output
# [[runnables]]
# name = "Generated project context"
# command = "python -m your_tool --print-context"
# description = "Generated project context"
# timeout_seconds = 60

[worktree]
# Project-root relative paths to symlink from the main checkout into spec worktrees.
# Every listed path is automatically added to .gitignore and must be safe to keep untracked.
# Typical examples are .env, .claude, .venv, node_modules, or deps. Use care with manifests and lock files such as pyproject.toml, package.json, or bun.lock; list them only when the project deliberately treats them as local-only.
symlink_paths = [".claude"]

[harness]
update_interval_days = 3

[branches]
dev = "dev"
main = "main"
test = "test"
# [branches.noswitch_branches]
# company_xyz = "main"
'''


def section_exists(content: str, section: str) -> bool:
    return re.search(rf"^\[{re.escape(section)}\]\s*$", content, re.MULTILINE) is not None


def section_declared(content: str, section: str) -> bool:
    return re.search(rf"^\s*#?\s*\[{re.escape(section)}\]\s*$", content, re.MULTILINE) is not None


def array_table_declared(content: str, name: str) -> bool:
    return re.search(rf"^\s*#?\s*\[\[{re.escape(name)}\]\]\s*$", content, re.MULTILINE) is not None


def key_declared(content: str, section: str, key: str) -> bool:
    lines = content.splitlines()
    in_section = False
    section_header = f"[{section}]"

    for line in lines:
        stripped = line.strip()
        uncommented = stripped[1:].strip() if stripped.startswith("#") else stripped
        if uncommented == section_header:
            in_section = True
            continue
        if in_section and uncommented.startswith("["):
            return False
        if in_section and re.match(rf"^{re.escape(key)}\s*=", uncommented):
            return True

    return False


def append_if_missing(content: str, chunk: str) -> str:
    if content and not content.endswith("\n"):
        content += "\n"
    if content.strip():
        content += "\n"
    return content + chunk.rstrip() + "\n"


def insert_key(content: str, section: str, line: str) -> str:
    lines = content.splitlines()
    section_header = f"[{section}]"

    for index, current in enumerate(lines):
        if current.strip() != section_header:
            continue

        insert_at = index + 1
        while insert_at < len(lines) and not lines[insert_at].strip().startswith("["):
            insert_at += 1
        lines.insert(insert_at, line)
        return "\n".join(lines) + "\n"

    return append_if_missing(content, f"{section_header}\n{line}")


def find_section_key_line(lines: list[str], section: str, key: str) -> int | None:
    in_section = False
    section_header = f"[{section}]"

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == section_header:
            in_section = True
            continue
        if in_section and stripped.startswith("["):
            return None
        if in_section and re.match(rf"^{re.escape(key)}\s*=", stripped):
            return index
    return None


def _matching_comment_start(lines: list[str], key_index: int, block: tuple[str, ...]) -> int | None:
    block_start = key_index - len(block)
    if block_start < 0:
        return None
    if tuple(line.strip() for line in lines[block_start:key_index]) == block:
        return block_start
    return None


def apply_key_comment_patch(content: str, patch: ConfigKeyCommentPatch) -> str:
    lines = content.splitlines()
    key_index = find_section_key_line(lines, patch.section, patch.key)
    if key_index is None:
        return content

    comment_start = _matching_comment_start(lines, key_index, patch.comment_lines)
    if comment_start is not None:
        return content

    for legacy_block in patch.legacy_comment_blocks:
        comment_start = _matching_comment_start(lines, key_index, legacy_block)
        if comment_start is None:
            continue
        lines[comment_start:key_index] = patch.comment_lines
        return "\n".join(lines).rstrip() + "\n"

    lines[key_index:key_index] = patch.comment_lines
    return "\n".join(lines).rstrip() + "\n"


def apply_config_patches(content: str) -> str:
    for patch in CONFIG_PATCHES:
        content = apply_key_comment_patch(content, patch)
    return content


def ensure_optional_onboard_config_block(content: str) -> str:
    missing_blocks = [
        block
        for name, block in OPTIONAL_ONBOARD_CONFIG_BLOCKS.items()
        if not array_table_declared(content, name)
    ]
    if not missing_blocks:
        return content
    return append_if_missing(content, "\n\n".join(missing_blocks))


def ensure_commented_runnable_name_scaffold(content: str) -> str:
    lines = content.splitlines()
    changed = False
    for index, line in enumerate(lines):
        if line.strip() != "# [[runnables]]":
            continue

        next_index = index + 1
        has_name = False
        while next_index < len(lines):
            stripped = lines[next_index].strip()
            if re.match(r"^#?\s*\[\[?[^\]]+\]?\]\s*$", stripped):
                break
            if re.match(r"^#\s*name\s*=", stripped):
                has_name = True
                break
            next_index += 1

        if not has_name:
            lines.insert(index + 1, '# name = "Generated project context"')
            changed = True

    if not changed:
        return content
    return "\n".join(lines).rstrip() + "\n"


def upsert_config(path: Path, project_name: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_config(project_name))
        print("Created managed file: .agent_core/config.toml")
        return

    content = path.read_text()
    original_content = content

    if not section_declared(content, "project"):
        content = append_if_missing(
            content,
            f'''[project]
name = "{project_name}"
description = """
Add your project description here.
"""''',
        )
    else:
        if section_exists(content, "project") and not key_declared(content, "project", "name"):
            content = insert_key(content, "project", f'name = "{project_name}"')
        if section_exists(content, "project") and not key_declared(content, "project", "description"):
            content = insert_key(
                content,
                "project",
                'description = """\nAdd your project description here.\n"""',
            )

    if not section_declared(content, "worktree"):
        content = append_if_missing(
            content,
            '''[worktree]
# Project-root relative paths to symlink from the main checkout into spec worktrees.
# Every listed path is automatically added to .gitignore and must be safe to keep untracked.
# Typical examples are .env, .claude, .venv, node_modules, or deps. Use care with manifests and lock files such as pyproject.toml, package.json, or bun.lock; list them only when the project deliberately treats them as local-only.
symlink_paths = [".claude"]''',
        )
    elif section_exists(content, "worktree") and not key_declared(content, "worktree", "symlink_paths"):
        content = insert_key(
            content,
            "worktree",
            'symlink_paths = [".claude"]',
        )

    if not section_declared(content, "harness"):
        content = append_if_missing(
            content,
            '''[harness]
update_interval_days = 3''',
        )
    elif section_exists(content, "harness") and not key_declared(
        content,
        "harness",
        "update_interval_days",
    ):
        content = insert_key(content, "harness", "update_interval_days = 3")

    if not section_declared(content, "branches"):
        content = append_if_missing(
            content,
            '''[branches]
dev = "dev"
main = "main"
test = "test"
# [branches.noswitch_branches]
# company_xyz = "main"''',
        )
    else:
        if section_exists(content, "branches") and not key_declared(content, "branches", "dev"):
            content = insert_key(content, "branches", 'dev = "dev"')
        if section_exists(content, "branches") and not key_declared(content, "branches", "main"):
            content = insert_key(content, "branches", 'main = "main"')
        if section_exists(content, "branches") and not key_declared(content, "branches", "test"):
            content = insert_key(content, "branches", 'test = "test"')

    content = ensure_optional_onboard_config_block(content)
    content = ensure_commented_runnable_name_scaffold(content)
    content = apply_config_patches(content)
    if content != original_content:
        path.write_text(content)
        print("Updated managed file: .agent_core/config.toml")


def read_toml(path: Path) -> dict[str, object]:
    try:
        with open(path, "rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def ensure_state_dirs(state_dir: Path) -> None:
    for name in ("", "specs", "todos", "memories", "logs", "docs"):
        path = state_dir / name
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            display_path = ".agent_core" if not name else f".agent_core/{name}"
            print(f"Created managed directory: {display_path}")


def ensure_config(config_file: Path, target_root: Path) -> bool:
    created = not config_file.exists()
    upsert_config(config_file, target_root.name)
    return created


def symlink_ignore_entries(config_file: Path) -> list[str]:
    config = read_toml(config_file)
    worktree_value = config.get("worktree")
    if not isinstance(worktree_value, dict):
        return []
    worktree = cast(dict[str, object], worktree_value)
    paths = worktree.get("symlink_paths")
    if not isinstance(paths, list):
        return []

    entries: list[str] = []
    for value in paths:
        if not isinstance(value, str):
            continue
        path = value.strip().strip("/")
        if not path:
            continue
        entries.extend([path, f"{path}/"])
    return entries


def ensure_symlink_paths_ignored(config_file: Path, gitignore_file: Path) -> None:
    entries = symlink_ignore_entries(config_file)
    if not entries:
        return

    existing = gitignore_file.read_text().splitlines() if gitignore_file.exists() else []
    seen = {line.strip() for line in existing}
    missing = [entry for entry in entries if entry not in seen]
    if not missing:
        return

    lines = existing[:]
    if lines and lines[-1].strip():
        lines.append("")
    lines.append("# Agent Core worktree symlinks")
    lines.extend(missing)
    gitignore_file.write_text("\n".join(lines).rstrip() + "\n")
    print("Updated .gitignore: added configured worktree symlink ignores: " + ", ".join(missing))


def ensure_agent_core_tmp_ignored(gitignore_file: Path) -> None:
    existing = gitignore_file.read_text().splitlines() if gitignore_file.exists() else []
    changed = False
    lines: list[str] = []

    for line in existing:
        if line.strip() == LEGACY_AGENT_CORE_TMP_IGNORE_ENTRY:
            lines.append(AGENT_CORE_TMP_IGNORE_ENTRY)
            changed = True
            continue
        lines.append(line)

    seen = {line.strip() for line in lines}
    if AGENT_CORE_TMP_IGNORE_ENTRY not in seen:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(AGENT_CORE_TMP_IGNORE_ENTRY)
        changed = True

    if changed:
        gitignore_file.write_text("\n".join(lines).rstrip() + "\n")
        print("Updated .gitignore: ensured .agent_core/tmp/ is ignored.")


def branch_names(config_file: Path) -> tuple[str, str, str]:
    config = read_toml(config_file)
    branches_value = config.get("branches")
    if not isinstance(branches_value, dict):
        fail("Missing required [branches] key(s): dev, test, main")
    branches = cast(dict[str, object], branches_value)
    missing = [name for name in ("dev", "test", "main") if not branches.get(name)]
    if missing:
        fail(f"Missing required [branches] key(s): {', '.join(missing)}")
    return str(branches["dev"]), str(branches["test"]), str(branches["main"])


def set_branch_names(config_file: Path, dev: str, test: str, main: str) -> None:
    values = {"dev": dev, "test": test, "main": main}
    lines = config_file.read_text().splitlines()
    section_index = None

    for index, line in enumerate(lines):
        if line.strip() == "[branches]":
            section_index = index
            break

    if section_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("[branches]")
        section_index = len(lines) - 1

    section_end = section_index + 1
    while section_end < len(lines) and not lines[section_end].strip().startswith("["):
        section_end += 1

    present: set[str] = set()
    for index in range(section_index + 1, section_end):
        match = re.match(r"^(\s*)(dev|test|main)\s*=", lines[index])
        if match is None:
            continue
        key = match.group(2)
        present.add(key)
        lines[index] = f"{key} = {json.dumps(values[key])}"

    insert_at = section_end
    for key in ("dev", "test", "main"):
        if key in present:
            continue
        lines.insert(insert_at, f"{key} = {json.dumps(values[key])}")
        insert_at += 1

    config_file.write_text("\n".join(lines).rstrip() + "\n")


def git_ref_exists(target_root: Path, ref: str) -> bool:
    return run_git(target_root, ["show-ref", "--verify", "--quiet", ref], check=False).returncode == 0


def has_origin(target_root: Path) -> bool:
    return run_git(target_root, ["remote", "get-url", "origin"], check=False).returncode == 0


def local_branch_exists(target_root: Path, branch: str) -> bool:
    return git_ref_exists(target_root, f"refs/heads/{branch}")


def remote_branch_exists(target_root: Path, branch: str) -> bool:
    return git_ref_exists(target_root, f"refs/remotes/origin/{branch}")


def fetch_origin_if_available(target_root: Path) -> bool:
    origin_exists = has_origin(target_root)
    if origin_exists:
        result = run_git(target_root, ["fetch", "--prune", "origin"], check=False)
        if result.returncode != 0:
            fail("Error: failed to fetch origin while validating protected branches.")
    return origin_exists


def rev_parse(target_root: Path, revision: str) -> str:
    return git_stdout(target_root, ["rev-parse", revision])


def is_ancestor(target_root: Path, ancestor: str, descendant: str) -> bool:
    return run_git(target_root, ["merge-base", "--is-ancestor", ancestor, descendant], check=False).returncode == 0


def branches_are_aligned(target_root: Path, branch: str) -> bool:
    if not remote_branch_exists(target_root, branch):
        return True
    return rev_parse(target_root, branch) == rev_parse(target_root, f"origin/{branch}")


def ensure_branch_names_are_distinct(config_file: Path) -> None:
    dev, test, main = branch_names(config_file)
    if len({dev, test, main}) != 3:
        fail("Error: configured main, test, and dev branch names must be distinct.")


def ensure_current_branch(target_root: Path, branch: str, action: str) -> None:
    current = current_branch(target_root)
    if current != branch:
        fail(f"Error: {action} must run from '{branch}'. Current branch: {current}")


def ensure_local_branch_from_remote_or_fail(target_root: Path, branch: str) -> None:
    if local_branch_exists(target_root, branch):
        return
    if remote_branch_exists(target_root, branch):
        run_git(target_root, ["branch", "--track", branch, f"origin/{branch}"])
        return
    fail(f"Error: configured main branch must exist before setup can continue: {branch}")


def print_existing_branches(target_root: Path, origin_exists: bool) -> None:
    print("Existing branches:")

    local = run_git(
        target_root,
        ["for-each-ref", "--format=%(refname:short)", "refs/heads"],
    ).stdout.splitlines()
    if local:
        print("  Local:")
        for branch in sorted(local):
            print(f"    - {branch}")
    else:
        print("  Local: none")

    if not origin_exists:
        return

    remote = [
        branch
        for branch in run_git(
            target_root,
            ["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"],
        ).stdout.splitlines()
        if branch != "origin/HEAD"
    ]
    if remote:
        print("  Origin:")
        for branch in sorted(remote):
            print(f"    - {branch.removeprefix('origin/')}")
    else:
        print("  Origin: none")


def prompt_branch_mapping(target_root: Path, config_file: Path) -> None:
    dev, test, main = branch_names(config_file)
    print("Configured protected branch mapping:")
    print(f"  main -> {main}")
    print(f"  test -> {test}")
    print(f"  dev  -> {dev}")

    if not sys.stdin.isatty():
        print("No interactive terminal detected; keeping the configured branch mapping.")
        return

    print("Press Enter to keep each value, or type an existing/custom branch name.")
    candidate = input(f"main branch [{main}]: ").strip()
    if candidate:
        main = candidate
    candidate = input(f"test branch [{test}]: ").strip()
    if candidate:
        test = candidate
    candidate = input(f"dev branch [{dev}]: ").strip()
    if candidate:
        dev = candidate

    for branch in (main, test, dev):
        result = run_git(target_root, ["check-ref-format", "--branch", branch], check=False)
        if result.returncode != 0:
            fail(f"Error: invalid branch name: {branch}")

    set_branch_names(config_file, dev, test, main)
    print("Updated .agent_core/config.toml branch mapping.")


def ensure_branches_exist(target_root: Path, config_file: Path) -> None:
    ensure_git_repository(target_root)
    origin_exists = fetch_origin_if_available(target_root)

    dev, test, main = branch_names(config_file)
    if not local_branch_exists(target_root, main):
        if origin_exists and remote_branch_exists(target_root, main):
            run_git(target_root, ["branch", "--track", main, f"origin/{main}"])
        else:
            print("Configured protected branches are missing.")
            print_existing_branches(target_root, origin_exists)
            fail(f"Error: configured main branch must exist before setup can continue: {main}")

    if not local_branch_exists(target_root, test):
        if origin_exists and remote_branch_exists(target_root, test):
            run_git(target_root, ["branch", "--track", test, f"origin/{test}"])
        else:
            run_git(target_root, ["branch", test, main])
        print(f"Created local protected branch: {test}")

    if not local_branch_exists(target_root, dev):
        if origin_exists and remote_branch_exists(target_root, dev):
            run_git(target_root, ["branch", "--track", dev, f"origin/{dev}"])
        else:
            run_git(target_root, ["branch", dev, test])
        print(f"Created local protected branch: {dev}")

    for branch in (main, test, dev):
        if origin_exists and not remote_branch_exists(target_root, branch):
            result = run_git(target_root, ["push", "-u", "origin", f"{branch}:{branch}"], check=False)
            if result.returncode != 0:
                fail(f"Error: failed to create origin/{branch}.")
            print(f"Created origin protected branch: origin/{branch}")


def ensure_update_branch(target_root: Path, config_file: Path, update: bool) -> None:
    if not update:
        return

    dev, _test, _main = branch_names(config_file)
    current = run_git(target_root, ["branch", "--show-current"]).stdout.strip()
    if not current:
        fail("Error: setup --update must run on a named branch, not detached HEAD.")
    if current == dev or current.startswith(f"{dev}-"):
        return
    fail(
        f"Error: setup --update must run from the configured dev branch '{dev}' "
        f"or a '{dev}-*' spec branch. Current branch: {current}"
    )


def staged_changes_exist(target_root: Path) -> bool:
    return run_git(target_root, ["diff", "--cached", "--quiet"], check=False).returncode != 0


def status_path(line: str) -> str:
    value = line[2:].strip()
    if " -> " in value:
        value = value.rsplit(" -> ", 1)[1]
    return value.strip().strip('"')


def is_harness_managed_status_path(path: str) -> bool:
    return path == ".agent_core" or path.startswith(".agent_core/") or path in HARNESS_MANAGED_PATHS


def ensure_only_harness_managed_changes(target_root: Path) -> None:
    unexpected = [path for path in (status_path(line) for line in status_lines(target_root)) if not is_harness_managed_status_path(path)]
    if not unexpected:
        return
    eprint("Error: setup produced changes outside harness-managed paths:")
    for path in unexpected:
        eprint(f"  {path}")
    raise SetupError("Refusing to commit unexpected setup changes.")


def stage_harness_managed_paths(target_root: Path) -> None:
    ensure_only_harness_managed_changes(target_root)
    run_git(target_root, ["add", "-A"])


def commit_and_push_current_branch(target_root: Path, message: str, branch: str, origin_exists: bool) -> bool:
    stage_harness_managed_paths(target_root)
    if not staged_changes_exist(target_root):
        print("No harness commit was needed.")
        return False
    run_git(target_root, ["commit", "-m", message])
    print(f'Created commit on {branch}: "{message}"')
    if origin_exists:
        run_git(target_root, ["push", "-u", "origin", branch])
        print(f"Pushed {branch} to origin.")
    return True


def sync_branch_from_remote(target_root: Path, branch: str) -> None:
    if not remote_branch_exists(target_root, branch):
        return
    if branches_are_aligned(target_root, branch):
        return
    local = branch
    remote = f"origin/{branch}"
    if is_ancestor(target_root, local, remote):
        run_git(target_root, ["checkout", branch])
        run_git(target_root, ["merge", "--ff-only", remote])
        print(f"Fast-forwarded local {branch} to {remote}.")
        return
    if is_ancestor(target_root, remote, local):
        fail(f"Error: local '{branch}' has commits that are not on origin/{branch}. Push or inspect them before setup continues.")
    fail(f"Error: local '{branch}' and origin/{branch} have diverged. Resolve the divergence before setup continues.")


def rebase_current_branch(target_root: Path, branch: str, base: str) -> bool:
    before = rev_parse(target_root, "HEAD")
    result = run_git(target_root, ["rebase", base], check=False)
    if result.returncode != 0:
        run_git(target_root, ["rebase", "--abort"], check=False)
        message = result.stderr.strip() or result.stdout.strip() or "rebase failed"
        fail(f"Error: could not rebase '{branch}' onto '{base}'. {message}")
    after = rev_parse(target_root, "HEAD")
    return before != after


def ensure_branch_contains_base(target_root: Path, branch: str, base: str, origin_exists: bool) -> None:
    if not local_branch_exists(target_root, branch):
        if origin_exists and remote_branch_exists(target_root, branch):
            run_git(target_root, ["branch", "--track", branch, f"origin/{branch}"])
            print(f"Created local protected branch: {branch}")
        else:
            run_git(target_root, ["branch", branch, base])
            print(f"Created local protected branch: {branch}")

    sync_branch_from_remote(target_root, branch)
    run_git(target_root, ["checkout", branch])
    rebased = rebase_current_branch(target_root, branch, base)
    if rebased:
        print(f"Rebased {branch} onto {base}.")
    else:
        print(f"{branch} already contains {base}.")

    if origin_exists:
        if remote_branch_exists(target_root, branch):
            run_git(target_root, ["push", "--force-with-lease", "origin", branch])
        else:
            run_git(target_root, ["push", "-u", "origin", branch])
        print(f"Pushed {branch} to origin.")


def complete_initial_install_git_flow(target_root: Path, config_file: Path) -> None:
    _dev, _test, main = branch_names(config_file)
    ensure_branch_names_are_distinct(config_file)
    ensure_git_repository(target_root)
    origin_exists = fetch_origin_if_available(target_root)
    ensure_local_branch_from_remote_or_fail(target_root, main)
    ensure_current_branch(target_root, main, "agent harness install")
    if origin_exists and not branches_are_aligned(target_root, main):
        fail(f"Error: local '{main}' and origin/{main} must be aligned before installing the harness.")


def preflight_initial_install_git_flow(target_root: Path, config_file: Path) -> None:
    ensure_git_repository(target_root)
    ensure_clean_worktree(target_root, "install the agent harness")
    main = branch_names(config_file)[2] if config_file.exists() else "main"
    origin_exists = fetch_origin_if_available(target_root)
    ensure_current_branch(target_root, main, "agent harness install")
    if origin_exists and remote_branch_exists(target_root, main) and not branches_are_aligned(target_root, main):
        fail(f"Error: local '{main}' and origin/{main} must be aligned before installing the harness.")


def finalize_initial_install_git_flow(target_root: Path, config_file: Path) -> None:
    dev, test, main = branch_names(config_file)
    origin_exists = has_origin(target_root)
    commit_and_push_current_branch(target_root, INSTALL_COMMIT_MESSAGE, main, origin_exists)
    ensure_branch_contains_base(target_root, test, main, origin_exists)
    ensure_branch_contains_base(target_root, dev, test, origin_exists)
    checkout_branch = dev if origin_exists else main
    run_git(target_root, ["checkout", checkout_branch])
    if checkout_branch == dev:
        print(f"Checked out mission-control branch: {dev}")
    else:
        print(f"Checked out branch: {main}")


def is_python_cache_path(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def remove_python_cache_artifacts(root: Path, display_path: str) -> None:
    if not root.exists():
        return

    for cache_dir in sorted(
        (path for path in root.rglob("__pycache__") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        relative_path = cache_dir.relative_to(root)
        shutil.rmtree(cache_dir)
        print(f"Removed Python cache directory: {display_path}/{relative_path.as_posix()}")

    for cache_file in sorted(path for path in root.rglob("*.pyc") if path.is_file()):
        relative_path = cache_file.relative_to(root)
        cache_file.unlink()
        print(f"Removed Python cache file: {display_path}/{relative_path.as_posix()}")


def sync_managed_directory(source: Path, target: Path, display_path: str) -> None:
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        print(f"Created managed directory: {display_path}")

    source_files = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file() and not is_python_cache_path(path.relative_to(source))
    }
    target_files = {path.relative_to(target) for path in target.rglob("*") if path.is_file()}
    source_dirs = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_dir() and not is_python_cache_path(path.relative_to(source))
    }

    for relative_path in sorted(source_dirs):
        target_dir = target / relative_path
        if target_dir.exists():
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created managed directory: {display_path}/{relative_path.as_posix()}")

    for relative_path in sorted(source_files):
        source_file = source / relative_path
        target_file = target / relative_path
        display_file = f"{display_path}/{relative_path.as_posix()}"
        if not target_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"Created managed file: {display_file}")
            continue
        if target_file.read_bytes() == source_file.read_bytes():
            continue
        shutil.copy2(source_file, target_file)
        print(f"Updated managed file: {display_file}")

    for relative_path in sorted(target_files - source_files, reverse=True):
        target_file = target / relative_path
        target_file.unlink()
        print(f"Removed stale managed file: {display_path}/{relative_path.as_posix()}")

    target_dirs = {path.relative_to(target) for path in target.rglob("*") if path.is_dir()}
    stale_dirs = sorted(target_dirs - source_dirs, key=lambda path: len(path.parts), reverse=True)
    for relative_path in stale_dirs:
        target_dir = target / relative_path
        try:
            target_dir.rmdir()
        except OSError:
            continue
        print(f"Removed stale managed directory: {display_path}/{relative_path.as_posix()}")

    remove_python_cache_artifacts(target, display_path)


def install_harness(template_root: Path, state_dir: Path) -> None:
    sync_managed_directory(
        template_root / ".agent_core" / "harness",
        state_dir / "harness",
        ".agent_core/harness",
    )


def install_harness_readme(template_root: Path, state_dir: Path) -> None:
    source = template_root / "README.md"
    if not source.is_file():
        return
    target = state_dir / "README.md"
    existed = target.exists()
    if target.exists() and target.read_text() == source.read_text():
        return
    shutil.copyfile(source, target)
    print("Updated managed file: .agent_core/README.md" if existed else "Created managed file: .agent_core/README.md")


def toml_string(value: str) -> str:
    return json.dumps(value)


def render_user_mappings(data: dict[str, object]) -> str:
    lines = ["# GitHub username to git user mappings"]
    for username, value in sorted(data.items()):
        if isinstance(value, str):
            name = value
            email = None
        elif isinstance(value, dict):
            table = cast(dict[str, object], value)
            raw_name = table.get("name")
            if not isinstance(raw_name, str):
                fail(f"Invalid .agent_core/user_mappings.toml entry for {username}: missing string name")
            name = raw_name
            raw_email = table.get("email")
            email = raw_email if isinstance(raw_email, str) and raw_email else None
        else:
            fail(f"Invalid .agent_core/user_mappings.toml entry for {username}: expected string or table")

        lines.append("")
        lines.append(f"[{username}]")
        lines.append(f"name = {toml_string(name)}")
        if email:
            lines.append(f"email = {toml_string(email)}")
    return "\n".join(lines).rstrip() + "\n"


def ensure_user_mappings(state_dir: Path) -> None:
    path = state_dir / "user_mappings.toml"
    if not path.exists():
        path.write_text("# GitHub username to git user mappings\n")
        print("Created managed file: .agent_core/user_mappings.toml")
        return

    with open(path, "rb") as f:
        raw = tomllib.load(f)
    if not any(isinstance(value, str) for value in raw.values()):
        return

    path.write_text(render_user_mappings(raw))
    print("Updated managed file: .agent_core/user_mappings.toml")


def install_agents_file(template_root: Path, target_root: Path) -> None:
    target_file = target_root / "AGENTS.md"
    template = (template_root / "AGENTS.md").read_text().strip() + "\n"

    if not target_file.exists():
        target_file.write_text(template)
        return

    content = target_file.read_text()
    start_tag = CORE_START_TAG
    end_tag = CORE_END_TAG
    start_index = content.find(start_tag)
    end_index = content.find(end_tag)

    if start_index == -1 or end_index == -1 or end_index <= start_index:
        legacy_start_index = content.find(LEGACY_CORE_START_TAG)
        legacy_end_index = content.find(LEGACY_CORE_END_TAG)
        if legacy_start_index != -1 and legacy_end_index != -1 and legacy_end_index > legacy_start_index:
            start_tag = LEGACY_CORE_START_TAG
            end_tag = LEGACY_CORE_END_TAG
            start_index = legacy_start_index
            end_index = legacy_end_index

    if start_index != -1 and end_index != -1 and end_index > start_index:
        end_index += len(end_tag)
        updated = content[:start_index] + template.strip() + content[end_index:]
    else:
        updated = template + "\n" + content

    target_file.write_text(updated)


def ensure_claude_file(target_root: Path) -> None:
    target_file = target_root / "CLAUDE.md"
    if os.name == "nt":
        shutil.copyfile(target_root / "AGENTS.md", target_file)
        return
    if target_file.exists() or target_file.is_symlink():
        target_file.unlink()
    target_file.symlink_to("AGENTS.md")


def optional_doc_path(optional_docs_dir: Path, slug: str) -> Path | None:
    if "/" in slug or "\\" in slug or slug.startswith(".") or slug.endswith(".md"):
        return None
    path = optional_docs_dir / f"{slug}.md"
    if not path.is_file():
        return None
    return path


def docs_list(optional_docs_dir: Path) -> list[str]:
    return sorted(path.stem for path in optional_docs_dir.glob("*.md") if path.is_file())


def copy_optional_doc(optional_docs_dir: Path, state_dir: Path, slug: str) -> None:
    source = optional_doc_path(optional_docs_dir, slug)
    if source is None:
        eprint(f"Error: unknown optional doc: {slug}")
        eprint("Available docs:")
        for available in docs_list(optional_docs_dir):
            eprint(available)
        raise SystemExit(1)
    shutil.copyfile(source, state_dir / "docs" / source.name)


def docs_add(optional_docs_dir: Path, state_dir: Path, slugs: list[str]) -> None:
    if not slugs:
        eprint("Error: docs add requires at least one doc slug.")
        eprint(usage())
        raise SystemExit(1)

    (state_dir / "docs").mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        copy_optional_doc(optional_docs_dir, state_dir, slug)
        print(f"Added optional doc: {slug}")


def install_default_docs(optional_docs_dir: Path, state_dir: Path, slugs: list[str] | None = None) -> None:
    (state_dir / "docs").mkdir(parents=True, exist_ok=True)
    selected_slugs = list(DEFAULT_DOCS) if slugs is None else slugs
    for slug in selected_slugs:
        source = optional_doc_path(optional_docs_dir, slug)
        if source is None:
            continue
        target = state_dir / "docs" / source.name
        if target.exists():
            continue
        shutil.copyfile(source, target)
        print(f"Included optional doc: {slug}")


def docs_update(optional_docs_dir: Path, state_dir: Path, slugs: list[str]) -> None:
    (state_dir / "docs").mkdir(parents=True, exist_ok=True)
    if slugs:
        docs_add(optional_docs_dir, state_dir, slugs)
        return

    updated = False
    for source in sorted(optional_docs_dir.glob("*.md")):
        target = state_dir / "docs" / source.name
        if not target.exists():
            continue
        shutil.copyfile(source, target)
        print(f"Updated optional doc: {source.stem}")
        updated = True

    if not updated:
        print("No installed optional docs to update.")


def parse_doc_selection(value: str) -> list[str]:
    return [part for part in re.split(r"[\s,]+", value.strip()) if part]


def prompt_optional_docs(optional_docs_dir: Path) -> list[str]:
    available = docs_list(optional_docs_dir)
    if not available:
        return []

    default_docs = list(DEFAULT_DOCS)
    print("")
    print("Optional project docs are available:")
    for slug in available:
        marker = " (default)" if slug in DEFAULT_DOCS else ""
        print(f"  - {slug}{marker}")
    print("")
    print("Enter doc slugs separated by spaces or commas.")
    print("Press Enter to install the default docs, or enter 'none' to skip optional docs.")

    response = input("Optional docs> ").strip()
    if not response:
        return default_docs
    if response.lower() in {"none", "no", "skip"}:
        return []

    selected = parse_doc_selection(response)
    unknown = [slug for slug in selected if optional_doc_path(optional_docs_dir, slug) is None]
    if unknown:
        fail("Unknown optional doc slug(s): " + ", ".join(unknown))
    return selected


def remove_lines_exact(path: Path, entries: set[str]) -> None:
    if not path.exists():
        return
    lines = path.read_text().splitlines()
    kept = [line for line in lines if line.strip() not in entries]
    content = "\n".join(kept).rstrip()
    if content:
        path.write_text(content + "\n")
    else:
        path.unlink()


def uninstall_agents_file(target_root: Path) -> None:
    target_file = target_root / "AGENTS.md"
    if not target_file.exists():
        return
    content = target_file.read_text()
    for start_tag, end_tag in ((CORE_START_TAG, CORE_END_TAG), (LEGACY_CORE_START_TAG, LEGACY_CORE_END_TAG)):
        start_index = content.find(start_tag)
        end_index = content.find(end_tag)
        if start_index == -1 or end_index == -1 or end_index <= start_index:
            continue
        end_index += len(end_tag)
        updated = (content[:start_index] + content[end_index:]).strip()
        if updated:
            target_file.write_text(updated + "\n")
        else:
            target_file.unlink()
        print("Removed managed AGENTS.md instructions.")
        return


def uninstall_claude_file(target_root: Path) -> None:
    target_file = target_root / "CLAUDE.md"
    if not target_file.exists() and not target_file.is_symlink():
        return
    if target_file.is_symlink():
        if os.readlink(target_file) == "AGENTS.md":
            target_file.unlink()
            print("Removed managed CLAUDE.md symlink.")
        return
    agents_file = target_root / "AGENTS.md"
    if not agents_file.exists() or target_file.read_text() == agents_file.read_text():
        target_file.unlink()
        print("Removed managed CLAUDE.md file.")


def uninstall_gitignore_entries(config_file: Path, target_root: Path) -> None:
    entries = {AGENT_CORE_TMP_IGNORE_ENTRY, LEGACY_AGENT_CORE_TMP_IGNORE_ENTRY, "# Agent Core worktree symlinks"}
    if config_file.exists():
        entries.update(symlink_ignore_entries(config_file))
    remove_lines_exact(target_root / ".gitignore", entries)
    print("Removed managed .gitignore entries.")


def uninstall_local_files(target_root: Path) -> None:
    config_file = target_root / ".agent_core" / "config.toml"
    uninstall_gitignore_entries(config_file, target_root)
    state_dir = target_root / ".agent_core"
    if state_dir.exists():
        shutil.rmtree(state_dir)
        print("Removed .agent_core.")
    uninstall_agents_file(target_root)
    uninstall_claude_file(target_root)


def parse_github_repo(remote_url: str) -> tuple[str, str] | None:
    remote_url = remote_url.strip()
    if remote_url.startswith("git@github.com:"):
        path = remote_url.removeprefix("git@github.com:")
    elif remote_url.startswith("https://github.com/"):
        path = urllib.parse.urlparse(remote_url).path.lstrip("/")
    else:
        return None
    if path.endswith(".git"):
        path = path[:-4]
    owner, separator, repo = path.partition("/")
    if not owner or not separator or not repo:
        return None
    return owner, repo


def github_request(method: str, url: str, token: str, payload: dict[str, object] | None = None) -> tuple[int, object | None, dict[str, str]]:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode()
            parsed = json.loads(body) if body else None
            return response.status, parsed, dict(response.headers.items())
    except urllib.error.HTTPError as error:
        body = error.read().decode()
        try:
            parsed = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = body
        return error.code, parsed, dict(error.headers.items())


def next_link(headers: dict[str, str]) -> str | None:
    link_header = headers.get("Link") or headers.get("link")
    if not link_header:
        return None
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section:
            continue
        start = section.find("<")
        end = section.find(">")
        if start != -1 and end != -1 and end > start:
            return section[start + 1 : end]
    return None


def close_harness_issues(owner: str, repo: str, token: str, label: str) -> int:
    closed = 0
    encoded_label = urllib.parse.quote(label)
    url: str | None = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&labels={encoded_label}&per_page=100"
    while url is not None:
        status, parsed, headers = github_request("GET", url, token)
        if status >= 400:
            fail(f"Error: could not list GitHub issues for label '{label}'.")
        if not isinstance(parsed, list):
            break
        for item in parsed:
            if not isinstance(item, dict) or "pull_request" in item:
                continue
            issue = cast(dict[str, object], item)
            issue_url = issue.get("url")
            if not isinstance(issue_url, str):
                continue
            issue_status, _body, _headers = github_request("PATCH", issue_url, token, {"state": "closed"})
            if issue_status >= 400:
                fail(f"Error: could not close GitHub issue for label '{label}'.")
            closed += 1
        url = next_link(headers)
    return closed


def delete_github_label(owner: str, repo: str, token: str, label: str) -> bool:
    encoded_label = urllib.parse.quote(label, safe="")
    url = f"https://api.github.com/repos/{owner}/{repo}/labels/{encoded_label}"
    status, _body, _headers = github_request("DELETE", url, token)
    if status == 404:
        return False
    if status >= 400:
        fail(f"Error: could not delete GitHub label '{label}'.")
    return True


def cleanup_github_harness_state(target_root: Path, origin_exists: bool) -> None:
    if not origin_exists:
        return
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Skipped GitHub issue and label cleanup because GITHUB_TOKEN/GH_TOKEN is not set.")
        return
    remote_url = git_stdout(target_root, ["remote", "get-url", "origin"])
    repo = parse_github_repo(remote_url)
    if repo is None:
        print("Skipped GitHub issue and label cleanup because origin is not a GitHub repository URL.")
        return
    owner, name = repo
    closed = close_harness_issues(owner, name, token, "spec") + close_harness_issues(owner, name, token, "todo")
    deleted = sum(1 for label in HARNESS_GITHUB_LABELS if delete_github_label(owner, name, token, label))
    print(f"Closed {closed} harness GitHub issue(s).")
    print(f"Deleted {deleted} harness GitHub label(s).")


def delete_branch_refs(target_root: Path, branch: str, origin_exists: bool) -> None:
    if origin_exists and remote_branch_exists(target_root, branch):
        run_git(target_root, ["push", "origin", "--delete", branch])
        print(f"Deleted origin/{branch}.")
    if local_branch_exists(target_root, branch):
        run_git(target_root, ["branch", "-D", branch])
        print(f"Deleted local branch: {branch}")


def uninstall(target_root: Path) -> None:
    config_file = target_root / ".agent_core" / "config.toml"
    if not config_file.exists():
        fail("Error: .agent_core/config.toml was not found. This does not look like an installed Agent Core project.")
    dev, test, main = branch_names(config_file)
    ensure_branch_names_are_distinct(config_file)
    ensure_git_repository(target_root)
    ensure_clean_worktree(target_root, "uninstall the agent harness")
    origin_exists = fetch_origin_if_available(target_root)
    ensure_current_branch(target_root, main, "agent harness uninstall")
    if origin_exists and not branches_are_aligned(target_root, main):
        fail(f"Error: local '{main}' and origin/{main} must be aligned before uninstalling the harness.")
    try:
        confirmation = input(f"Type the exact uninstall confirmation phrase to delete Agent Core state and {test}/{dev}: ")
    except EOFError:
        fail("Error: uninstall requires interactive confirmation. No changes were made.")
    if confirmation != UNINSTALL_CONFIRMATION:
        fail("Error: uninstall confirmation did not match. No changes were made.")

    cleanup_github_harness_state(target_root, origin_exists)
    uninstall_local_files(target_root)
    commit_and_push_current_branch(target_root, UNINSTALL_COMMIT_MESSAGE, main, origin_exists)
    delete_branch_refs(target_root, dev, origin_exists)
    delete_branch_refs(target_root, test, origin_exists)
    print("Uninstalled project-local harness.")


def handle_docs_command(optional_docs_dir: Path, state_dir: Path, args: list[str]) -> None:
    subcommand = args[0] if args else ""
    if subcommand == "list":
        for slug in docs_list(optional_docs_dir):
            print(slug)
        return
    if subcommand == "add":
        docs_add(optional_docs_dir, state_dir, args[1:])
        return
    if subcommand == "update":
        docs_update(optional_docs_dir, state_dir, args[1:])
        return
    eprint(usage())
    raise SystemExit(1)


def upsert_last_updated_at(config_file: Path) -> None:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    content = config_file.read_text()

    if not section_exists(content, "harness"):
        config_file.write_text(append_if_missing(content, f'[harness]\nlast_updated_at = "{timestamp}"'))
        print("Updated managed file: .agent_core/config.toml")
        return

    lines = content.splitlines()
    in_section = False
    updated = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[harness]":
            in_section = True
            continue
        if in_section and stripped.startswith("["):
            lines.insert(index, f'last_updated_at = "{timestamp}"')
            updated = True
            break
        if in_section and re.match(r"^last_updated_at\s*=", stripped):
            lines[index] = f'last_updated_at = "{timestamp}"'
            updated = True
            break

    if in_section and not updated:
        lines.append(f'last_updated_at = "{timestamp}"')

    updated_content = "\n".join(lines).rstrip() + "\n"
    if updated_content != content:
        config_file.write_text(updated_content)
        print("Updated managed file: .agent_core/config.toml")


def install(template_root: Path, target_root: Path, update: bool) -> None:
    state_dir = target_root / ".agent_core"
    config_file = state_dir / "config.toml"
    optional_docs_dir = template_root / "optional_docs"
    selected_docs: list[str] | None = None

    if not update:
        preflight_initial_install_git_flow(target_root, config_file)
    if not update and sys.stdin.isatty():
        selected_docs = prompt_optional_docs(optional_docs_dir)
    ensure_state_dirs(state_dir)
    config_created = ensure_config(config_file, target_root)
    if config_created and not update and sys.stdin.isatty():
        prompt_branch_mapping(target_root, config_file)
    if not update:
        complete_initial_install_git_flow(target_root, config_file)
    ensure_agent_core_tmp_ignored(target_root / ".gitignore")
    ensure_symlink_paths_ignored(config_file, target_root / ".gitignore")
    if update:
        ensure_branches_exist(target_root, config_file)
        ensure_update_branch(target_root, config_file, update)
    install_harness(template_root, state_dir)
    install_harness_readme(template_root, state_dir)
    ensure_user_mappings(state_dir)
    install_agents_file(template_root, target_root)
    ensure_claude_file(target_root)
    if update:
        docs_update(optional_docs_dir, state_dir, [])
    install_default_docs(optional_docs_dir, state_dir, selected_docs)
    upsert_last_updated_at(config_file)
    if not update:
        finalize_initial_install_git_flow(target_root, config_file)
    print("Updated project-local harness." if update else "Installed project-local harness.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        usage=argparse.SUPPRESS,
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=usage(),
    )
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("command", nargs="?")
    parser.add_argument("subargs", nargs=argparse.REMAINDER)
    return parser.parse_args(normalize_argv(argv))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    target_root = Path.cwd()
    template_root, temp_dir = resolve_template_root()
    try:
        if args.command == "docs":
            handle_docs_command(template_root / "optional_docs", target_root / ".agent_core", args.subargs)
            return 0
        if args.uninstall:
            if args.command is not None or args.update:
                eprint(usage())
                return 1
            uninstall(target_root)
            return 0
        if args.command is not None:
            eprint(usage())
            return 1
        install(template_root, target_root, args.update)
        return 0
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SetupError as error:
        eprint(str(error))
        raise SystemExit(1) from error
