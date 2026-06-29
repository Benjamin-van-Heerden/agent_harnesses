import re
from pathlib import Path


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


def _strip_inline_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    result: list[str] = []

    for char in line:
        if escaped:
            result.append(char)
            escaped = False
            continue
        if char == "\\" and in_double:
            result.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            result.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            result.append(char)
            continue
        if char == "#" and not in_single and not in_double:
            break
        result.append(char)

    return "".join(result)


def _array_table_declared(content: str, name: str) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _strip_inline_comment(stripped).strip() == f"[[{name}]]":
            return True
    return False


def _append_if_missing(content: str, chunk: str) -> str:
    if content and not content.endswith("\n"):
        content += "\n"
    if content.strip():
        content += "\n"
    return content + chunk.rstrip() + "\n"


def _ensure_optional_onboard_config_block(content: str) -> str:
    missing_blocks = [
        block
        for name, block in OPTIONAL_ONBOARD_CONFIG_BLOCKS.items()
        if not _array_table_declared(content, name)
    ]
    if not missing_blocks:
        return content
    return _append_if_missing(content, "\n\n".join(missing_blocks))


def _ensure_commented_runnable_name_scaffold(content: str) -> str:
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


def run(project_root: Path) -> bool:
    config_file = project_root / ".agent_core" / "config.toml"
    if not config_file.exists():
        return False

    content = config_file.read_text()
    updated = _ensure_optional_onboard_config_block(content)
    updated = _ensure_commented_runnable_name_scaffold(updated)
    if updated == content:
        return False

    config_file.write_text(updated)
    print("Applied config patch: ensured optional onboard config scaffolds.")
    return True
