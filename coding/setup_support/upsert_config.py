import argparse
import re
from dataclasses import dataclass
from pathlib import Path


WORKTREE_SYMLINK_PATHS_COMMENT = (
    "# Project-root relative paths to symlink from the main checkout into spec worktrees.",
    "# Every listed path is automatically added to .gitignore and must be safe to keep untracked.",
    "# Typical examples are .env, .claude, .venv, node_modules, or deps. Use care with manifests and lock files such as pyproject.toml, package.json, or bun.lock; list them only when the project deliberately treats them as local-only.",
)
LEGACY_WORKTREE_SYMLINK_PATHS_COMMENT = "# Paths to symlink into worktrees instead of copying"


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
    return re.search(
        rf"^\s*#?\s*\[{re.escape(section)}\]\s*$",
        content,
        re.MULTILINE,
    ) is not None


def key_exists(content: str, section: str, key: str) -> bool:
    lines = content.splitlines()
    in_section = False
    section_header = f"[{section}]"

    for line in lines:
        stripped = line.strip()
        if stripped == section_header:
            in_section = True
            continue
        if in_section and stripped.startswith("["):
            return False
        if in_section and re.match(rf"^{re.escape(key)}\s*=", stripped):
            return True

    return False


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


def insert_after_section(content: str, section: str, chunk: str) -> str:
    lines = content.splitlines()
    section_header = f"[{section}]"

    for index, current in enumerate(lines):
        if current.strip() != section_header:
            continue

        insert_at = index + 1
        while insert_at < len(lines) and not lines[insert_at].strip().startswith("["):
            insert_at += 1
        while insert_at > index + 1 and lines[insert_at - 1].strip() == "":
            insert_at -= 1
        if insert_at < len(lines) and lines[insert_at].strip() != "":
            chunk = chunk.rstrip() + "\n"
        lines[insert_at:insert_at] = ["", *chunk.rstrip().splitlines()]
        return "\n".join(lines).rstrip() + "\n"

    return append_if_missing(content, chunk)


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

    path.write_text(apply_config_patches(content))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("project_name")
    args = parser.parse_args()
    upsert_config(Path(args.path), args.project_name)


if __name__ == "__main__":
    main()
