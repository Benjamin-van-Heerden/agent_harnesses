import tomllib
from pathlib import Path
from typing import Any


FILES_BLOCK = """# Files to include in onboard output
# [[files]]
# path = "README.md"
# description = "Practice overview and setup instructions"
"""

SRC_TREE_BLOCK = """# Directories whose tree structure is included in onboard output
[[tree_dirs]]
path = "src"
description = "Reusable Typst source"
"""


def _config_path(project_root: Path) -> Path:
    return project_root / ".praxis" / "config.toml"


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with open(path, "rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _has_files_config(text: str, data: dict[str, Any]) -> bool:
    files = data.get("files")
    return "[[files]]" in text or isinstance(files, list)


def _has_src_tree(data: dict[str, Any]) -> bool:
    tree_dirs = data.get("tree_dirs")
    if not isinstance(tree_dirs, list):
        return False
    for item in tree_dirs:
        if isinstance(item, dict) and item.get("path") == "src":
            return True
    return False


def _insert_before_harness(text: str, block: str) -> str:
    lines = text.rstrip().splitlines()
    insert_at = len(lines)
    for index, line in enumerate(lines):
        if line.strip() == "[harness]":
            insert_at = index
            break
    prefix = lines[:insert_at]
    suffix = lines[insert_at:]
    if prefix and prefix[-1].strip():
        prefix.append("")
    block_lines = block.strip().splitlines()
    updated = [*prefix, *block_lines]
    if suffix:
        updated.append("")
        updated.extend(suffix)
    return "\n".join(updated).rstrip() + "\n"


def needs_patch(project_root: Path) -> bool:
    path = _config_path(project_root)
    if not path.is_file():
        return False
    text = path.read_text()
    data = _read_toml(path)
    return not _has_files_config(text, data) or not _has_src_tree(data)


def run(project_root: Path) -> dict[str, object]:
    path = _config_path(project_root)
    if not path.is_file():
        return {"changed": False, "details": ["config missing"]}

    text = path.read_text()
    data = _read_toml(path)
    changed = False
    added: list[str] = []

    if not _has_files_config(text, data):
        text = _insert_before_harness(text, FILES_BLOCK)
        changed = True
        added.append("files")
        data = _read_toml_from_text(text)

    if not _has_src_tree(data):
        text = _insert_before_harness(text, SRC_TREE_BLOCK)
        changed = True
        added.append("tree_dirs:src")

    if changed:
        path.write_text(text)
    return {"changed": changed, "details": added}


def _read_toml_from_text(text: str) -> dict[str, Any]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
