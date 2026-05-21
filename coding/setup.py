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
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn, cast


REPO_ARCHIVE_URL = "https://github.com/Benjamin-van-Heerden/agent_harnesses/archive/refs/heads/main.zip"
TEMPLATE_SUBPATH = "coding"
CORE_START_TAG = "<AGENT_CORE>"
CORE_END_TAG = "</AGENT_CORE>"
DEFAULT_DOCS = ("coding_general", "coding_testing")
WORKTREE_SYMLINK_PATHS_COMMENT = (
    "# Project-root relative paths to symlink from the main checkout into spec worktrees.",
    "# Every listed path is automatically added to .gitignore and must be safe to keep untracked.",
    "# Typical examples are .env, .claude, .venv, node_modules, or deps. Use care with manifests and lock files such as pyproject.toml, package.json, or bun.lock; list them only when the project deliberately treats them as local-only.",
)
LEGACY_WORKTREE_SYMLINK_PATHS_COMMENT = "# Paths to symlink into worktrees instead of copying"
AGENT_CORE_TMP_IGNORE_ENTRY = ".agent_core/tmp/"
LEGACY_AGENT_CORE_TMP_IGNORE_ENTRY = ".agent_core/tmp"


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
    if shutil.which("git") is None:
        fail("Error: git is required but was not found on PATH.")
    if run_git(target_root, ["rev-parse", "--git-dir"], check=False).returncode != 0:
        fail("Error: setup must be run from an initialized git repository.")

    origin_exists = has_origin(target_root)
    if origin_exists:
        result = run_git(target_root, ["fetch", "--prune", "origin"], check=False)
        if result.returncode != 0:
            fail("Error: failed to fetch origin while validating protected branches.")

    if run_git(target_root, ["rev-parse", "--verify", "HEAD"], check=False).returncode != 0:
        fail("Error: setup requires at least one commit before protected branches can be created.")

    dev, test, main = branch_names(config_file)
    if not git_ref_exists(target_root, f"refs/heads/{main}"):
        if origin_exists and git_ref_exists(target_root, f"refs/remotes/origin/{main}"):
            run_git(target_root, ["branch", "--track", main, f"origin/{main}"])
        else:
            print("Configured protected branches are missing.")
            print_existing_branches(target_root, origin_exists)
            fail(f"Error: configured main branch must exist before setup can continue: {main}")

    if not git_ref_exists(target_root, f"refs/heads/{test}"):
        if origin_exists and git_ref_exists(target_root, f"refs/remotes/origin/{test}"):
            run_git(target_root, ["branch", "--track", test, f"origin/{test}"])
        else:
            run_git(target_root, ["branch", test, main])
        print(f"Created local protected branch: {test}")

    if not git_ref_exists(target_root, f"refs/heads/{dev}"):
        if origin_exists and git_ref_exists(target_root, f"refs/remotes/origin/{dev}"):
            run_git(target_root, ["branch", "--track", dev, f"origin/{dev}"])
        else:
            run_git(target_root, ["branch", dev, test])
        print(f"Created local protected branch: {dev}")

    for branch in (main, test, dev):
        if origin_exists and not git_ref_exists(target_root, f"refs/remotes/origin/{branch}"):
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


def sync_managed_directory(source: Path, target: Path, display_path: str) -> None:
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
        print(f"Created managed directory: {display_path}")

    source_files = {path.relative_to(source) for path in source.rglob("*") if path.is_file()}
    target_files = {path.relative_to(target) for path in target.rglob("*") if path.is_file()}
    source_dirs = {path.relative_to(source) for path in source.rglob("*") if path.is_dir()}

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


def ensure_user_mappings(state_dir: Path) -> None:
    path = state_dir / "user_mappings.toml"
    if not path.exists():
        path.write_text("# GitHub username to git user mappings\n")
        print("Created managed file: .agent_core/user_mappings.toml")


def install_agents_file(template_root: Path, target_root: Path) -> None:
    target_file = target_root / "AGENTS.md"
    template = (template_root / "AGENTS.md").read_text().strip() + "\n"

    if not target_file.exists():
        target_file.write_text(template)
        return

    content = target_file.read_text()
    start_index = content.find(CORE_START_TAG)
    end_index = content.find(CORE_END_TAG)

    if start_index != -1 and end_index != -1 and end_index > start_index:
        end_index += len(CORE_END_TAG)
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


def install_default_docs(optional_docs_dir: Path, state_dir: Path) -> None:
    (state_dir / "docs").mkdir(parents=True, exist_ok=True)
    for slug in DEFAULT_DOCS:
        source = optional_doc_path(optional_docs_dir, slug)
        if source is None:
            continue
        target = state_dir / "docs" / source.name
        if target.exists():
            continue
        shutil.copyfile(source, target)
        print(f"Included default doc: {slug}")


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

    ensure_state_dirs(state_dir)
    config_created = ensure_config(config_file, target_root)
    if config_created and not update and sys.stdin.isatty():
        prompt_branch_mapping(target_root, config_file)
    ensure_agent_core_tmp_ignored(target_root / ".gitignore")
    ensure_symlink_paths_ignored(config_file, target_root / ".gitignore")
    ensure_branches_exist(target_root, config_file)
    ensure_update_branch(target_root, config_file, update)
    install_harness(template_root, state_dir)
    install_harness_readme(template_root, state_dir)
    ensure_user_mappings(state_dir)
    install_agents_file(template_root, target_root)
    ensure_claude_file(target_root)
    if update:
        docs_update(optional_docs_dir, state_dir, [])
    install_default_docs(optional_docs_dir, state_dir)
    upsert_last_updated_at(config_file)
    print("Updated project-local harness." if update else "Installed project-local harness.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        usage=argparse.SUPPRESS,
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=usage(),
    )
    parser.add_argument("--update", action="store_true")
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
