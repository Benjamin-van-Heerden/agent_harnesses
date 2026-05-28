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
CORE_TAGS = (
    ("<AGENT_CORE>", "</AGENT_CORE>"),
    ("<core_instructions>", "</core_instructions>"),
)
LEGAL_GITIGNORE_START = "# >>> legal agent core gitignore >>>"
LEGAL_GITIGNORE_END = "# <<< legal agent core gitignore <<<"
DEFAULT_DOCS = (
    "legal_harness_typst_basic_reference",
    "legal_harness_typst_soft_typesystem_and_house_rules",
)
OPTIONAL_DOC_SUFFIXES = (".md", ".typ")


class SetupError(Exception):
    pass


REQUIRED_EXTERNAL_COMMANDS = ("git", "typst")


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

Docs commands copy optional docs into .praxis/docs/.
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
    fail(
        f"Error: template subdirectory '{TEMPLATE_SUBPATH}' not found in repository archive."
    )


def run_git(
    target_root: Path, args: list[str], check: bool = False
) -> subprocess.CompletedProcess[str]:
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


def command_version_available(command: str) -> bool:
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def missing_external_commands() -> list[str]:
    return [
        command
        for command in REQUIRED_EXTERNAL_COMMANDS
        if not command_version_available(command)
    ]


def external_dependency_guidance(command: str) -> list[str]:
    if command == "git":
        return [
            "Git is required for local practice-state checkpoints.",
            "Install Git:",
            "  Windows: winget install --id Git.Git",
            "  macOS: xcode-select --install, or brew install git",
            "  Linux: use your distribution package manager, for example sudo apt install git",
        ]
    if command == "typst":
        return [
            "Typst is required for legal document compilation.",
            "Install Typst:",
            "  Windows: winget install --id Typst.Typst",
            "  macOS: brew install typst",
            "  Linux: use your distribution package manager, or download Typst from https://github.com/typst/typst/releases",
        ]
    return [f"Install {command} and ensure it is available on PATH."]


def require_external_dependencies() -> None:
    missing = missing_external_commands()
    if not missing:
        return

    lines = [
        "Error: missing required external dependencies.",
        "Setup checks these commands with --version before installing the legal harness.",
    ]
    for command in missing:
        lines.append("")
        lines.append(f"Missing required command: {command}")
        lines.extend(external_dependency_guidance(command))
    lines.append("")
    lines.append(
        "Install the missing command(s), ensure they are available on PATH, then rerun setup."
    )
    fail("\n".join(lines))


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
    print("Created managed file: .praxis/config.toml")


def upsert_last_updated_at(config_file: Path) -> None:
    timestamp = (
        datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    content = (
        config_file.read_text()
        if config_file.exists()
        else default_config(config_file.parent.parent.name)
    )
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
            print("Updated managed file: .praxis/config.toml")
            return
        if in_harness and stripped.startswith("last_updated_at"):
            lines[index] = f'last_updated_at = "{timestamp}"'
            config_file.write_text("\n".join(lines).rstrip() + "\n")
            print("Updated managed file: .praxis/config.toml")
            return

    if in_harness:
        lines.append(f'last_updated_at = "{timestamp}"')
    else:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["[harness]", f'last_updated_at = "{timestamp}"'])
    config_file.write_text("\n".join(lines).rstrip() + "\n")
    print("Updated managed file: .praxis/config.toml")


def ensure_state_dirs(state_dir: Path, target_root: Path) -> None:
    dirs = (
        state_dir,
        state_dir / "core_docs",
        state_dir / "docs",
        state_dir / "tmp",
        state_dir / "local_context",
        state_dir / "local_context" / "memories",
        state_dir / "local_context" / "logs",
        state_dir / "local_context" / "workflows",
        state_dir / "todos" / "open",
        state_dir / "todos" / "claimed",
        target_root / "ZZ_CLIENTS",
        target_root / "UNBOUND",
        target_root / "UNBOUND" / "open",
        target_root / "UNBOUND" / "closed",
        target_root / "WIP",
        target_root / "WIP" / "drafts",
        target_root / "WIP" / "experiments",
        target_root / "assets",
        target_root / "src" / "components",
        target_root / "src" / "constants",
        target_root / "src" / "templates",
        target_root / "src" / "types",
    )
    for path in dirs:
        if path.exists():
            continue
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path.relative_to(target_root).as_posix()}")


def wip_readme() -> str:
    return """# WIP workspace

Use this workspace for non-matter drafting, template/style experiments, and workflow iteration.

- Put non-matter drafts under `WIP/drafts/`.
- Put template, style, and workflow experiments under `WIP/experiments/`.
- Create organized subfolders for each piece of work instead of dropping loose files directly into `WIP/`.
- Matter-specific drafts belong in the matter folder, along with matter-specific source material.
"""


def ensure_wip_guidance(target_root: Path) -> None:
    path = target_root / "WIP" / "README.md"
    if path.exists():
        return
    path.write_text(wip_readme())
    print("Created lawyer-owned file: WIP/README.md")


def ensure_git_repo(target_root: Path) -> None:
    if run_git(target_root, ["rev-parse", "--git-dir"]).returncode == 0:
        return
    run_git(target_root, ["init"], check=True)
    print("Initialized local git repository.")


def legal_gitignore_block() -> str:
    return f"""{LEGAL_GITIGNORE_START}
# Generated by legal Agent Core setup. Keep git focused on text-based practice context.

# Compiled documents and common office/binary formats
*.p.pdf
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

# Temporary harness output
.praxis/tmp/
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
        start_index = content.find(LEGAL_GITIGNORE_START)
        end_index = content.find(LEGAL_GITIGNORE_END) + len(LEGAL_GITIGNORE_END)
        updated = content[:start_index] + block + content[end_index:]
        if updated != content:
            path.write_text(updated.rstrip() + "\n")
            print("Updated .gitignore: refreshed legal Agent Core block.")
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
    source_files = {
        path.relative_to(source) for path in source.rglob("*") if path.is_file()
    }
    target_files = {
        path.relative_to(target) for path in target.rglob("*") if path.is_file()
    }
    source_dirs = {
        path.relative_to(source) for path in source.rglob("*") if path.is_dir()
    }

    for relative_path in sorted(source_dirs):
        (target / relative_path).mkdir(parents=True, exist_ok=True)

    for relative_path in sorted(source_files):
        source_file = source / relative_path
        target_file = target / relative_path
        copy_or_update(
            source_file, target_file, f"{display_path}/{relative_path.as_posix()}"
        )

    for relative_path in sorted(target_files - source_files, reverse=True):
        target_file = target / relative_path
        target_file.unlink()
        print(f"Removed stale managed file: {display_path}/{relative_path.as_posix()}")

    target_dirs = {
        path.relative_to(target) for path in target.rglob("*") if path.is_dir()
    }
    for relative_path in sorted(
        target_dirs - source_dirs, key=lambda path: len(path.parts), reverse=True
    ):
        target_dir = target / relative_path
        try:
            target_dir.rmdir()
        except OSError:
            continue
        print(
            f"Removed stale managed directory: {display_path}/{relative_path.as_posix()}"
        )


def install_harness(template_root: Path, state_dir: Path) -> None:
    sync_managed_directory(
        template_root / ".agent_core" / "harness",
        state_dir / "harness",
        ".praxis/harness",
    )


def install_harness_readme(template_root: Path, state_dir: Path) -> None:
    copy_or_update(
        template_root / ".agent_core" / "README.md",
        state_dir / "README.md",
        ".praxis/README.md",
    )


def install_practice_defaults(template_root: Path, state_dir: Path) -> None:
    copy_if_missing(
        template_root / ".agent_core" / "local_context" / "lawyer_profile.md",
        state_dir / "local_context" / "lawyer_profile.md",
        ".praxis/local_context/lawyer_profile.md",
    )
    copy_if_missing(
        template_root / ".agent_core" / "core_docs" / "legal_context.typ",
        state_dir / "core_docs" / "legal_context.typ",
        ".praxis/core_docs/legal_context.typ",
    )
    copy_or_update(
        template_root / ".agent_core" / "docs" / "typst_detailed_reference.typ",
        state_dir / "docs" / "typst_detailed_reference.typ",
        ".praxis/docs/typst_detailed_reference.typ",
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
            print(f"Removed renamed managed doc: .praxis/docs/{name}")


def handle_docs_command(
    optional_docs_dir: Path, state_dir: Path, args: list[str]
) -> None:
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


def install_typst_source(template_root: Path, target_root: Path) -> None:
    source_root = template_root / "src"
    target_src = target_root / "src"
    if not source_root.is_dir():
        return
    for source_file in sorted(
        path for path in source_root.rglob("*") if path.is_file()
    ):
        relative_path = source_file.relative_to(source_root)
        copy_or_update(
            source_file, target_src / relative_path, f"src/{relative_path.as_posix()}"
        )


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
    state_dir = target_root / ".praxis"
    optional_docs_dir = template_root / "optional_docs"
    require_external_dependencies()
    if update and not state_dir.exists():
        fail(
            "Error: no legal harness state found. Run setup.py without --update first."
        )

    ensure_state_dirs(state_dir, target_root)
    ensure_wip_guidance(target_root)
    ensure_config(state_dir / "config.toml", target_root)
    ensure_git_repo(target_root)
    ensure_gitignore(target_root)
    install_harness(template_root, state_dir)
    install_harness_readme(template_root, state_dir)
    install_practice_defaults(template_root, state_dir)
    if update:
        docs_update(optional_docs_dir, state_dir, [])
    install_default_docs(optional_docs_dir, state_dir)
    remove_renamed_managed_docs(state_dir)
    install_typst_source(template_root, target_root)
    install_agents_file(template_root, target_root)
    ensure_claude_file(target_root)
    upsert_last_updated_at(state_dir / "config.toml")
    print(
        "Updated native legal harness." if update else "Installed native legal harness."
    )
    print("You must run: python -B .praxis/harness/main.py onboard")


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
            handle_docs_command(
                template_root / "optional_docs", target_root / ".praxis", args.subargs
            )
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
