import re
from pathlib import Path


WORKTREE_SYMLINK_PATHS_COMMENT = (
    "# Project-root relative paths to symlink from the main checkout into spec worktrees.",
    "# Every listed path is automatically added to .gitignore and must be safe to keep untracked.",
    "# Typical examples are .env, .claude, .venv, node_modules, or deps. Use care with manifests and lock files such as pyproject.toml, package.json, or bun.lock; list them only when the project deliberately treats them as local-only.",
)
LEGACY_WORKTREE_SYMLINK_PATHS_COMMENT = "# Paths to symlink into worktrees instead of copying"


def _find_section_key_line(lines: list[str], section: str, key: str) -> int | None:
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


def _apply_worktree_comment_patch(content: str) -> str:
    lines = content.splitlines()
    key_index = _find_section_key_line(lines, "worktree", "symlink_paths")
    if key_index is None:
        return content

    comment_start = _matching_comment_start(lines, key_index, WORKTREE_SYMLINK_PATHS_COMMENT)
    if comment_start is not None:
        return content

    comment_start = _matching_comment_start(lines, key_index, (LEGACY_WORKTREE_SYMLINK_PATHS_COMMENT,))
    if comment_start is not None:
        lines[comment_start:key_index] = WORKTREE_SYMLINK_PATHS_COMMENT
        return "\n".join(lines).rstrip() + "\n"

    lines[key_index:key_index] = WORKTREE_SYMLINK_PATHS_COMMENT
    return "\n".join(lines).rstrip() + "\n"


def run(project_root: Path) -> bool:
    config_file = project_root / ".agent_core" / "config.toml"
    if not config_file.exists():
        return False

    content = config_file.read_text()
    updated = _apply_worktree_comment_patch(content)
    if updated == content:
        return False

    config_file.write_text(updated)
    print("Applied config patch: refreshed worktree symlink comments.")
    return True
