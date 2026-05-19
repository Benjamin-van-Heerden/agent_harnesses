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
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn, cast


REPO_ARCHIVE_URL = "https://github.com/Benjamin-van-Heerden/agent_harnesses/archive/refs/heads/main.zip"
TEMPLATE_SUBPATH = "coding"
CORE_START_TAG = "<AGENT_CORE>"
CORE_END_TAG = "</AGENT_CORE>"
DEFAULT_DOCS = ("coding_general", "coding_testing")


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
symlink_paths = [".agent_core/docs/data", ".claude"]

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


def upsert_config(path: Path, project_name: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_config(project_name))
        return

    content = path.read_text()

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
symlink_paths = [".agent_core/docs/data", ".claude"]''',
        )
    elif section_exists(content, "worktree") and not key_declared(content, "worktree", "symlink_paths"):
        content = insert_key(
            content,
            "worktree",
            'symlink_paths = [".agent_core/docs/data", ".claude"]',
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

    path.write_text(content)


def read_toml(path: Path) -> dict[str, object]:
    try:
        with open(path, "rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def ensure_state_dirs(state_dir: Path) -> None:
    for name in ("", "specs", "todos", "memories", "logs", "docs"):
        (state_dir / name).mkdir(parents=True, exist_ok=True)


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
    if current == dev:
        return
    fail(f"Error: setup --update must run from the configured dev branch '{dev}'. Current branch: {current}")


def install_harness(template_root: Path, state_dir: Path) -> None:
    source = template_root / ".agent_core" / "harness"
    target = state_dir / "harness"
    if target.exists():
        shutil.rmtree(target)
    state_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def ensure_user_mappings(state_dir: Path) -> None:
    path = state_dir / "user_mappings.toml"
    if not path.exists():
        path.write_text("# GitHub username to git user mappings\n")


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

    config_file.write_text("\n".join(lines).rstrip() + "\n")


def install(template_root: Path, target_root: Path, update: bool) -> None:
    state_dir = target_root / ".agent_core"
    config_file = state_dir / "config.toml"
    optional_docs_dir = template_root / "optional_docs"

    ensure_state_dirs(state_dir)
    config_created = ensure_config(config_file, target_root)
    if config_created and not update and sys.stdin.isatty():
        prompt_branch_mapping(target_root, config_file)
    ensure_symlink_paths_ignored(config_file, target_root / ".gitignore")
    ensure_branches_exist(target_root, config_file)
    ensure_update_branch(target_root, config_file, update)
    install_harness(template_root, state_dir)
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
