#!/usr/bin/env python3
import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn


REPO_ARCHIVE_URL = "https://github.com/Benjamin-van-Heerden/agent_harnesses/archive/refs/heads/main.zip"
TEMPLATE_SUBPATH = "legal"
CORE_TAGS = (("<AGENT_CORE>", "</AGENT_CORE>"), ("<core_instructions>", "</core_instructions>"))
LEGAL_GITIGNORE_START = "# >>> legal agent core gitignore >>>"
LEGAL_GITIGNORE_END = "# <<< legal agent core gitignore <<<"
DEFAULT_DOCS = (
    "legal_harness_function",
    "legal_harness_typst_basic_reference",
    "legal_harness_typst_soft_typesystem_and_house_rules",
)
OPTIONAL_DOC_SUFFIXES = (".md", ".typ")


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

Install or refresh the native legal Agent Core harness in the current directory.
Setup refreshes managed runtime/reference files and preserves lawyer-owned practice state.

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

    temp_dir = tempfile.TemporaryDirectory(prefix="legal-agent-core-setup-")
    eprint("Fetching latest legal harness template...")
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


def run_git(target_root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
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
Describe this legal practice workspace.
"""

[harness]
name = "legal"
local_git_snapshots = true
update_interval_days = 3

[legal]
jurisdiction = ""
'''


def ensure_config(config_file: Path, target_root: Path) -> None:
    if config_file.exists():
        return
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(default_config(target_root.name))
    print("Created managed file: .agent_core/config.toml")


def upsert_last_updated_at(config_file: Path) -> None:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    content = config_file.read_text() if config_file.exists() else default_config(config_file.parent.parent.name)
    lines = content.splitlines()
    in_harness = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[harness]":
            in_harness = True
            continue
        if in_harness and stripped.startswith("["):
            lines.insert(index, f'last_updated_at = "{timestamp}"')
            config_file.write_text("\n".join(lines).rstrip() + "\n")
            print("Updated managed file: .agent_core/config.toml")
            return
        if in_harness and stripped.startswith("last_updated_at"):
            lines[index] = f'last_updated_at = "{timestamp}"'
            config_file.write_text("\n".join(lines).rstrip() + "\n")
            print("Updated managed file: .agent_core/config.toml")
            return

    if in_harness:
        lines.append(f'last_updated_at = "{timestamp}"')
    else:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["[harness]", f'last_updated_at = "{timestamp}"'])
    config_file.write_text("\n".join(lines).rstrip() + "\n")
    print("Updated managed file: .agent_core/config.toml")


def ensure_state_dirs(state_dir: Path, target_root: Path) -> None:
    dirs = (
        state_dir,
        state_dir / "docs",
        state_dir / "practice",
        state_dir / "practice" / "memories",
        state_dir / "practice" / "logs",
        state_dir / "todos" / "open",
        state_dir / "todos" / "claimed",
        state_dir / "practice" / "templates",
        target_root / ".agent_docs",
        target_root / "clients",
        target_root / "src" / "constants",
        target_root / "src" / "functions",
        target_root / "src" / "templates",
        target_root / "src" / "templates" / "components",
        target_root / "src" / "templates" / "components" / "assets",
        target_root / "src" / "types",
        target_root / "functions",
        target_root / "templates",
    )
    for path in dirs:
        if path.exists():
            continue
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path.relative_to(target_root).as_posix()}")


def ensure_git_repo(target_root: Path) -> None:
    if shutil.which("git") is None:
        print("Git not found on PATH. Local snapshot support is disabled until git is installed.")
        return
    if run_git(target_root, ["rev-parse", "--git-dir"]).returncode == 0:
        return
    run_git(target_root, ["init"], check=True)
    print("Initialized local git repository.")


def legal_gitignore_block() -> str:
    return f"""{LEGAL_GITIGNORE_START}
# Generated by legal Agent Core setup. Keep git focused on text-based practice context.

# Compiled documents and common office/binary formats
*.pdf
*.doc
*.docx
*.xls
*.xlsx
*.ppt
*.pptx
*.odt
*.ods
*.odp
*.rtf
*.pages
*.numbers
*.key

# Office lock/temp files
~$*
.~lock.*

# Local OS noise
.DS_Store
Thumbs.db
desktop.ini
{LEGAL_GITIGNORE_END}
"""


def ensure_gitignore(target_root: Path) -> None:
    path = target_root / ".gitignore"
    block = legal_gitignore_block().rstrip()
    if not path.exists():
        path.write_text(block + "\n")
        print("Created managed file: .gitignore")
        return

    content = path.read_text()
    if LEGAL_GITIGNORE_START in content and LEGAL_GITIGNORE_END in content:
        return

    if content and not content.endswith("\n"):
        content += "\n"
    if content.strip():
        content += "\n"
    path.write_text(content + block + "\n")
    print("Updated .gitignore: added legal Agent Core block.")


def copy_if_missing(source: Path, target: Path, display_path: str) -> None:
    if target.exists() or not source.is_file():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"Created lawyer-owned file: {display_path}")


def copy_or_update(source: Path, target: Path, display_path: str) -> None:
    if not source.is_file():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() == source.read_bytes():
        return
    existed = target.exists()
    shutil.copy2(source, target)
    print(f"{'Updated' if existed else 'Created'} managed file: {display_path}")


def copy_tree_missing(source: Path, target: Path, display_path: str) -> None:
    if not source.is_dir():
        return
    for source_file in sorted(path for path in source.rglob("*") if path.is_file()):
        relative_path = source_file.relative_to(source)
        target_file = target / relative_path
        if target_file.exists():
            continue
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        print(f"Created lawyer-owned file: {display_path}/{relative_path.as_posix()}")


def sync_managed_directory(source: Path, target: Path, display_path: str) -> None:
    if not source.is_dir():
        fail(f"Error: managed source directory is missing: {source}")

    target.mkdir(parents=True, exist_ok=True)
    source_files = {path.relative_to(source) for path in source.rglob("*") if path.is_file()}
    target_files = {path.relative_to(target) for path in target.rglob("*") if path.is_file()}
    source_dirs = {path.relative_to(source) for path in source.rglob("*") if path.is_dir()}

    for relative_path in sorted(source_dirs):
        (target / relative_path).mkdir(parents=True, exist_ok=True)

    for relative_path in sorted(source_files):
        source_file = source / relative_path
        target_file = target / relative_path
        copy_or_update(source_file, target_file, f"{display_path}/{relative_path.as_posix()}")

    for relative_path in sorted(target_files - source_files, reverse=True):
        target_file = target / relative_path
        target_file.unlink()
        print(f"Removed stale managed file: {display_path}/{relative_path.as_posix()}")

    target_dirs = {path.relative_to(target) for path in target.rglob("*") if path.is_dir()}
    for relative_path in sorted(target_dirs - source_dirs, key=lambda path: len(path.parts), reverse=True):
        target_dir = target / relative_path
        try:
            target_dir.rmdir()
        except OSError:
            continue
        print(f"Removed stale managed directory: {display_path}/{relative_path.as_posix()}")


def install_harness(template_root: Path, state_dir: Path) -> None:
    sync_managed_directory(template_root / ".agent_core" / "harness", state_dir / "harness", ".agent_core/harness")


def install_harness_readme(template_root: Path, state_dir: Path) -> None:
    copy_or_update(template_root / ".agent_core" / "README.md", state_dir / "README.md", ".agent_core/README.md")


def install_practice_defaults(template_root: Path, state_dir: Path) -> None:
    copy_if_missing(
        template_root / ".agent_core" / "practice" / "lawyer_profile.md",
        state_dir / "practice" / "lawyer_profile.md",
        ".agent_core/practice/lawyer_profile.md",
    )
    copy_if_missing(
        template_root / ".agent_core" / "docs" / "legal_context.typ",
        state_dir / "docs" / "legal_context.typ",
        ".agent_core/docs/legal_context.typ",
    )
    copy_tree_missing(
        template_root / ".agent_core" / "practice" / "templates",
        state_dir / "practice" / "templates",
        ".agent_core/practice/templates",
    )


def optional_doc_path(optional_docs_dir: Path, slug: str) -> Path | None:
    if "/" in slug or "\\" in slug or slug.startswith(".") or Path(slug).suffix:
        return None
    matches = [
        optional_docs_dir / f"{slug}{suffix}"
        for suffix in OPTIONAL_DOC_SUFFIXES
        if (optional_docs_dir / f"{slug}{suffix}").is_file()
    ]
    return matches[0] if len(matches) == 1 else None


def docs_list(optional_docs_dir: Path) -> list[str]:
    return sorted(
        path.stem
        for path in optional_docs_dir.glob("*")
        if path.is_file() and path.suffix in OPTIONAL_DOC_SUFFIXES
    )


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
    for source in sorted(optional_docs_dir.glob("*")):
        if not source.is_file() or source.suffix not in OPTIONAL_DOC_SUFFIXES:
            continue
        target = state_dir / "docs" / source.name
        if not target.exists():
            continue
        shutil.copyfile(source, target)
        print(f"Updated optional doc: {source.stem}")
        updated = True

    if not updated:
        print("No installed optional docs to update.")


def remove_renamed_managed_docs(state_dir: Path) -> None:
    for name in (
        "typst_basic_reference.typ",
        "typst_soft_typesystem_and_house_rules_updated.typ",
    ):
        path = state_dir / "docs" / name
        if path.exists():
            path.unlink()
            print(f"Removed renamed managed doc: .agent_core/docs/{name}")


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


def install_agent_docs(template_root: Path, state_dir: Path) -> None:
    copy_or_update(
        template_root / ".agent_docs" / "typst_detailed_reference.typ",
        state_dir.parent / ".agent_docs" / "typst_detailed_reference.typ",
        ".agent_docs/typst_detailed_reference.typ",
    )


def install_typst_source(template_root: Path, target_root: Path) -> None:
    source_root = template_root / "src"
    target_src = target_root / "src"
    if not source_root.is_dir():
        return
    for source_file in sorted(path for path in source_root.rglob("*") if path.is_file()):
        relative_path = source_file.relative_to(source_root)
        copy_or_update(source_file, target_src / relative_path, f"src/{relative_path.as_posix()}")


def read_frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator:
            data[key.strip()] = value.strip().strip("'\"")
    return data


def legacy_todo_target(target_root: Path, source_file: Path, claimed: bool) -> Path:
    frontmatter = read_frontmatter(source_file)
    matter = frontmatter.get("matter", "").strip()
    if matter and matter != "null":
        matter_dir = target_root / matter
        if matter_dir.is_dir():
            bucket = "claimed" if claimed else ""
            return matter_dir / "info" / "todos" / bucket / source_file.name if bucket else matter_dir / "info" / "todos" / source_file.name
    bucket = "claimed" if claimed else "open"
    return target_root / ".agent_core" / "todos" / bucket / source_file.name


def copy_legacy_todos(target_root: Path, legacy_todos: Path) -> None:
    if not legacy_todos.is_dir():
        return
    for source_file in sorted(path for path in legacy_todos.glob("*.md") if path.is_file()):
        target_file = legacy_todo_target(target_root, source_file, claimed=False)
        copy_if_missing(source_file, target_file, target_file.relative_to(target_root).as_posix())
    claimed_dir = legacy_todos / "claimed"
    if not claimed_dir.is_dir():
        return
    for source_file in sorted(path for path in claimed_dir.glob("*.md") if path.is_file()):
        target_file = legacy_todo_target(target_root, source_file, claimed=True)
        copy_if_missing(source_file, target_file, target_file.relative_to(target_root).as_posix())


def migrate_legacy_agent_rules(target_root: Path) -> None:
    legacy_root = target_root / "agent_rules"
    if not legacy_root.is_dir():
        return

    state_dir = target_root / ".agent_core"
    copy_if_missing(
        legacy_root / "lawyer_profile.md",
        state_dir / "practice" / "lawyer_profile.md",
        ".agent_core/practice/lawyer_profile.md",
    )
    copy_if_missing(
        legacy_root / "docs" / "core" / "legal_context.typ",
        state_dir / "docs" / "legal_context.typ",
        ".agent_core/docs/legal_context.typ",
    )
    copy_tree_missing(legacy_root / "memories", state_dir / "practice" / "memories", ".agent_core/practice/memories")
    copy_tree_missing(legacy_root / "log", state_dir / "practice" / "logs", ".agent_core/practice/logs")
    copy_tree_missing(legacy_root / "skeletons", state_dir / "practice" / "templates", ".agent_core/practice/templates")
    copy_legacy_todos(target_root, legacy_root / "todos")
    print("Detected legacy agent_rules state. Copied durable legacy state into native .agent_core locations.")


def managed_block_bounds(content: str) -> tuple[int, int] | None:
    for start_tag, end_tag in CORE_TAGS:
        start_index = content.find(start_tag)
        end_index = content.find(end_tag)
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return start_index, end_index + len(end_tag)
    return None


def install_agents_file(template_root: Path, target_root: Path) -> None:
    target_file = target_root / "AGENTS.md"
    template = (template_root / "AGENTS.md").read_text().strip() + "\n"
    if not target_file.exists():
        target_file.write_text(template)
        print("Created managed file: AGENTS.md")
        return

    content = target_file.read_text()
    bounds = managed_block_bounds(content)
    if bounds is None:
        updated = template + "\n" + content
    else:
        start_index, end_index = bounds
        updated = content[:start_index] + template.strip() + content[end_index:]
    if updated != content:
        target_file.write_text(updated.rstrip() + "\n")
        print("Updated managed block: AGENTS.md")


def ensure_claude_file(target_root: Path) -> None:
    target_file = target_root / "CLAUDE.md"
    if os.name == "nt":
        shutil.copyfile(target_root / "AGENTS.md", target_file)
        print("Updated managed file: CLAUDE.md")
        return
    if target_file.exists() or target_file.is_symlink():
        target_file.unlink()
    target_file.symlink_to("AGENTS.md")
    print("Updated managed file: CLAUDE.md")


def install(template_root: Path, target_root: Path, update: bool) -> None:
    state_dir = target_root / ".agent_core"
    optional_docs_dir = template_root / "optional_docs"
    if update and not state_dir.exists() and not (target_root / "agent_rules").exists():
        fail("Error: no legal harness state found. Run setup.py without --update first.")

    ensure_state_dirs(state_dir, target_root)
    ensure_config(state_dir / "config.toml", target_root)
    ensure_git_repo(target_root)
    ensure_gitignore(target_root)
    migrate_legacy_agent_rules(target_root)
    install_harness(template_root, state_dir)
    install_harness_readme(template_root, state_dir)
    install_practice_defaults(template_root, state_dir)
    if update:
        docs_update(optional_docs_dir, state_dir, [])
    install_default_docs(optional_docs_dir, state_dir)
    remove_renamed_managed_docs(state_dir)
    install_agent_docs(template_root, state_dir)
    install_typst_source(template_root, target_root)
    install_agents_file(template_root, target_root)
    ensure_claude_file(target_root)
    upsert_last_updated_at(state_dir / "config.toml")
    print("Updated native legal harness." if update else "Installed native legal harness.")
    print("You must run: python -B .agent_core/harness/main.py onboard")


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
