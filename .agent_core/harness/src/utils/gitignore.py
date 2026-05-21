from pathlib import Path

from src.config.models import AgentCoreConfig


HEADER = "# Agent Core worktree symlinks"
TMP_IGNORE_ENTRY = ".agent_core/tmp/"
LEGACY_TMP_IGNORE_ENTRY = ".agent_core/tmp"


def _normalized_symlink_path(value: str) -> str:
    path = Path(value.strip())
    if path.is_absolute() or path == Path(".") or ".." in path.parts:
        raise ValueError(f"Invalid worktree symlink path in config: {value}")
    normalized = path.as_posix().rstrip("/")
    if not normalized:
        raise ValueError(f"Invalid worktree symlink path in config: {value}")
    return normalized


def symlink_ignore_entries(config: AgentCoreConfig) -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()
    for value in config.worktree.symlink_paths:
        path = _normalized_symlink_path(value)
        for entry in (path, f"{path}/"):
            if entry in seen:
                continue
            entries.append(entry)
            seen.add(entry)
    return entries


def ensure_symlink_paths_ignored(config: AgentCoreConfig, gitignore_file: Path) -> list[str]:
    entries = symlink_ignore_entries(config)
    if not entries:
        return []

    existing = gitignore_file.read_text().splitlines() if gitignore_file.exists() else []
    seen = {line.strip() for line in existing}
    missing = [entry for entry in entries if entry not in seen]
    if not missing:
        return []

    lines = existing[:]
    if lines and lines[-1].strip():
        lines.append("")
    if HEADER not in seen:
        lines.append(HEADER)
    lines.extend(missing)
    gitignore_file.write_text("\n".join(lines).rstrip() + "\n")
    return missing


def ensure_agent_core_tmp_ignored(gitignore_file: Path) -> bool:
    existing = gitignore_file.read_text().splitlines() if gitignore_file.exists() else []
    changed = False
    lines: list[str] = []

    for line in existing:
        if line.strip() == LEGACY_TMP_IGNORE_ENTRY:
            lines.append(TMP_IGNORE_ENTRY)
            changed = True
            continue
        lines.append(line)

    seen = {line.strip() for line in lines}
    if TMP_IGNORE_ENTRY not in seen:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(TMP_IGNORE_ENTRY)
        changed = True

    if changed:
        gitignore_file.write_text("\n".join(lines).rstrip() + "\n")
    return changed
