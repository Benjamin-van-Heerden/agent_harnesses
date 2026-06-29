from pathlib import Path


RETIRED_DEFAULT_DOCS = ("coding_general.md", "coding_testing.md")


def run(project_root: Path) -> bool:
    docs_dir = project_root / ".agent_core" / "docs"
    changed = False
    for filename in RETIRED_DEFAULT_DOCS:
        path = docs_dir / filename
        if not path.exists():
            continue
        path.unlink()
        print(f"Removed retired default doc: {filename}")
        changed = True
    return changed
