from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.state.models import MemoryRecord
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_slug
from src.utils.markdown import read_markdown


def parse_memory(path: Path) -> MemoryRecord:
    document = read_markdown(path)
    title = ""
    for line in document.body.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return MemoryRecord(
        slug=document.frontmatter.get("slug", path.stem),
        created=document.frontmatter.get("created", ""),
        title=title,
        path=path,
    )


def create_memory(slug: str, title: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_slug(slug)
    path = paths.memories_root / f"{slug}.md"
    if path.exists():
        raise FileExistsError(f"memory already exists: {slug}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_template(
            "memory",
            paths,
            SLUG=slug,
            TODAY=today(),
            TITLE=title,
            CONTENT="_TODO_",
        )
    )
    return path


def list_memories(paths: ProjectPaths = PROJECT_PATHS) -> list[MemoryRecord]:
    if not paths.memories_root.is_dir():
        return []
    return [parse_memory(path) for path in sorted(paths.memories_root.glob("*.md"))]
