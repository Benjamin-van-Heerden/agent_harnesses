import re
from pathlib import Path


TARGET_LINE = "update_interval_days = 1"
TARGET_SECTION = "harness"
TARGET_KEY = "update_interval_days"


def _find_section_header(lines: list[str], section: str) -> int | None:
    header = f"[{section}]"
    for index, line in enumerate(lines):
        if line.strip() == header:
            return index
    return None


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


def _apply_daily_update_interval(content: str) -> str:
    lines = content.splitlines()
    key_index = _find_section_key_line(lines, TARGET_SECTION, TARGET_KEY)
    if key_index is not None:
        if lines[key_index].strip() == TARGET_LINE:
            return content
        lines[key_index] = TARGET_LINE
        return "\n".join(lines).rstrip() + "\n"

    section_index = _find_section_header(lines, TARGET_SECTION)
    if section_index is not None:
        insert_at = section_index + 1
        while insert_at < len(lines) and not lines[insert_at].strip().startswith("["):
            insert_at += 1
        lines.insert(insert_at, TARGET_LINE)
        return "\n".join(lines).rstrip() + "\n"

    if lines and lines[-1].strip():
        lines.append("")
    lines.extend([f"[{TARGET_SECTION}]", TARGET_LINE])
    return "\n".join(lines).rstrip() + "\n"


def run(project_root: Path) -> bool:
    config_file = project_root / ".agent_core" / "config.toml"
    if not config_file.exists():
        return False

    content = config_file.read_text()
    updated = _apply_daily_update_interval(content)
    if updated == content:
        return False

    config_file.write_text(updated)
    print("Applied config patch: set harness update interval to 1 day.")
    return True
