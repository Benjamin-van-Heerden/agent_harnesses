from pathlib import Path

IGNORE_ENTRY = ".agent_core/**/.DS_Store"


def run(project_root: Path) -> bool:
    gitignore_file = project_root / ".gitignore"
    existing = gitignore_file.read_text().splitlines() if gitignore_file.exists() else []
    lines = [line for line in existing if line.strip() != IGNORE_ENTRY]
    lines.append(IGNORE_ENTRY)
    if lines == existing:
        return False

    gitignore_file.write_text("\n".join(lines).rstrip() + "\n")
    print("Applied .gitignore patch: ignored .DS_Store files throughout .agent_core/.")
    return True
