from pathlib import Path


AGENT_CORE_STATE_IGNORE_BLOCK = (
    "# Agent Core state",
    "!.agent_core/",
    "!.agent_core/**",
    ".agent_core/tmp/",
    ".agent_core/tmp/**",
    ".cache/pycache/",
    ".cache/pycache/**",
)
LEGACY_AGENT_CORE_TMP_IGNORE_ENTRY = ".agent_core/tmp"


def run(project_root: Path) -> bool:
    gitignore_file = project_root / ".gitignore"
    existing = gitignore_file.read_text().splitlines() if gitignore_file.exists() else []
    lines: list[str] = []

    for line in existing:
        stripped = line.strip()
        if stripped in AGENT_CORE_STATE_IGNORE_BLOCK or stripped == LEGACY_AGENT_CORE_TMP_IGNORE_ENTRY:
            continue
        lines.append(line)

    if lines and lines[-1].strip():
        lines.append("")
    lines.extend(AGENT_CORE_STATE_IGNORE_BLOCK)

    changed = lines != existing
    if changed:
        gitignore_file.write_text("\n".join(lines).rstrip() + "\n")
        print("Applied .gitignore patch: ensured Agent Core state is tracked except .agent_core/tmp/ and .cache/pycache/ is ignored.")
    return changed
