import shutil
from pathlib import Path
from typing import cast

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.models.frontmatter import TodoFrontmatter, TodoPriority
from src.state.matters import resolve_matter
from src.state.models import TodoRecord
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_slug, validate_todo_priority
from src.utils.markdown import MarkdownDocument, frontmatter_get, frontmatter_set, read_markdown, write_markdown


def _title_from_body(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def parse_todo(path: Path) -> TodoRecord:
    document = read_markdown(path)
    return TodoRecord(
        slug=frontmatter_get(path, "slug") or path.stem,
        created=frontmatter_get(path, "created"),
        status=frontmatter_get(path, "status"),
        priority=frontmatter_get(path, "priority"),
        matter=frontmatter_get(path, "matter") or "null",
        title=_title_from_body(document.body),
        path=path,
    )


def global_todo_path(slug: str, claimed: bool = False, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    bucket = paths.global_claimed_todos_root if claimed else paths.global_open_todos_root
    return bucket / f"{slug}.md"


def matter_todo_path(matter_dir: Path, slug: str, claimed: bool = False) -> Path:
    bucket = matter_dir / "info" / "todos" / "claimed" if claimed else matter_dir / "info" / "todos"
    return bucket / f"{slug}.md"


def create_todo(
    slug: str,
    title: str,
    priority: str = "normal",
    matter_ref: str = "",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    validate_slug(slug)
    validate_todo_priority(priority)
    matter_path: str | None = None
    matter_dir: Path | None = None
    if matter_ref:
        matter_dir = resolve_matter(matter_ref, paths)
        matter_path = str(matter_dir.relative_to(paths.project_root))

    path = matter_todo_path(matter_dir, slug) if matter_dir is not None else global_todo_path(slug, paths=paths)
    if path.exists():
        raise FileExistsError(f"todo already exists: {slug}")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = render_template("todo", paths, TITLE=title, DESCRIPTION="_TODO_")
    write_markdown(
        path,
        MarkdownDocument(
            frontmatter=TodoFrontmatter(
                slug=slug,
                created=today(),
                priority=cast(TodoPriority, priority),
                matter=matter_path,
            ).to_dict(),
            body=body,
        ),
    )
    return path


def claim_todo(slug: str, matter_ref: str = "", paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_slug(slug)
    if matter_ref:
        matter_dir = resolve_matter(matter_ref, paths)
        source = matter_todo_path(matter_dir, slug)
        destination = matter_todo_path(matter_dir, slug, claimed=True)
    else:
        source = global_todo_path(slug, paths=paths)
        destination = global_todo_path(slug, claimed=True, paths=paths)

    if not source.is_file():
        raise FileNotFoundError(f"open todo not found: {slug}")
    if destination.is_file():
        raise FileExistsError(f"already claimed: {slug}")

    frontmatter_set(source, "status", "claimed")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    return destination


def list_global_todos(paths: ProjectPaths = PROJECT_PATHS) -> list[TodoRecord]:
    if not paths.global_open_todos_root.is_dir():
        return []
    return [parse_todo(path) for path in sorted(paths.global_open_todos_root.glob("*.md"))]


def list_matter_todos(matter_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> list[TodoRecord]:
    matter_dir = resolve_matter(matter_ref, paths)
    todos_dir = matter_dir / "info" / "todos"
    if not todos_dir.is_dir():
        return []
    return [parse_todo(path) for path in sorted(todos_dir.glob("*.md"))]


def list_claimed_global_todos(paths: ProjectPaths = PROJECT_PATHS) -> list[TodoRecord]:
    if not paths.global_claimed_todos_root.is_dir():
        return []
    return [parse_todo(path) for path in sorted(paths.global_claimed_todos_root.glob("*.md"))]


def list_claimed_matter_todos(matter_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> list[TodoRecord]:
    matter_dir = resolve_matter(matter_ref, paths)
    todos_dir = matter_dir / "info" / "todos" / "claimed"
    if not todos_dir.is_dir():
        return []
    return [parse_todo(path) for path in sorted(todos_dir.glob("*.md"))]


def list_all_todos(paths: ProjectPaths = PROJECT_PATHS) -> list[TodoRecord]:
    records = list_global_todos(paths) + list_claimed_global_todos(paths)
    for matter_dir in sorted(paths.clients_root.glob("*/matters/*/*")):
        if not matter_dir.is_dir():
            continue
        matter_ref = str(matter_dir.relative_to(paths.project_root))
        records.extend(list_matter_todos(matter_ref, paths))
        records.extend(list_claimed_matter_todos(matter_ref, paths))
    return sorted(records, key=lambda record: (record.matter or "", record.status, record.priority, record.slug))
