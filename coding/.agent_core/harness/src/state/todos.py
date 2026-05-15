from __future__ import annotations

from pathlib import Path

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import TodoFrontmatter, TodoStatus, create_todo_frontmatter, now_iso
from src.state.models import Todo
from src.utils.markdown import read_markdown, slugify, write_markdown


def _claimed_dir() -> Path:
    return PROJECT_PATHS.todos_dir / "claimed"


def _open_path(slug: str) -> Path:
    return PROJECT_PATHS.todos_dir / f"{slug}.md"


def _claimed_path(slug: str) -> Path:
    return _claimed_dir() / f"{slug}.md"


def _item_path(slug: str) -> Path:
    open_path = _open_path(slug)
    if open_path.exists():
        return open_path

    claimed_path = _claimed_path(slug)
    if claimed_path.exists():
        return claimed_path

    return open_path


def _to_todo(slug: str, metadata: object, body: str) -> Todo:
    frontmatter = TodoFrontmatter.model_validate(metadata)
    return Todo(slug=slug, body=body, frontmatter=frontmatter)


def create(
    title: str,
    description: str = "",
    issue_id: int | None = None,
    issue_url: str | None = None,
) -> Path:
    slug = slugify(title)
    path = _item_path(slug)
    if path.exists():
        raise ValueError(f"Todo '{slug}' already exists")

    metadata = create_todo_frontmatter(title, issue_id=issue_id, issue_url=issue_url)
    write_markdown(path, metadata.to_dict(), description)
    return path


def create_with_metadata(title: str, metadata: TodoFrontmatter, description: str = "") -> Path:
    slug = slugify(title)
    path = _item_path(slug)
    if path.exists():
        return path
    write_markdown(path, metadata.to_dict(), description)
    return path


def get(slug: str) -> Todo | None:
    path = _item_path(slug)
    if not path.exists():
        return None
    metadata, body = read_markdown(path)
    return _to_todo(slug, metadata, body)


def list_all(status: TodoStatus | None = None) -> list[Todo]:
    records: list[Todo] = []
    for directory in [PROJECT_PATHS.todos_dir, _claimed_dir()]:
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if not path.is_file() or path.suffix != ".md":
                continue
            metadata, body = read_markdown(path)
            record = _to_todo(path.stem, metadata, body)
            if status is not None and record.status != status:
                continue
            records.append(record)

    records.sort(key=lambda item: item.frontmatter.created_at, reverse=True)
    return records


def _write_frontmatter(slug: str, frontmatter: TodoFrontmatter) -> None:
    path = _item_path(slug)
    if not path.exists():
        raise ValueError(f"Todo '{slug}' not found")
    record = get(slug)
    if record is None:
        raise ValueError(f"Todo '{slug}' not found")
    write_markdown(path, frontmatter.to_dict(), record.body)


def update_issue(slug: str, issue_id: int, issue_url: str) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Todo '{slug}' not found")
    frontmatter = record.frontmatter.model_copy(update={"issue_id": issue_id, "issue_url": issue_url})
    _write_frontmatter(slug, frontmatter)


def claim(slug: str, claimed_by: str) -> Path:
    path = _item_path(slug)
    if not path.exists():
        raise ValueError(f"Todo '{slug}' not found")

    record = get(slug)
    if record is None:
        raise ValueError(f"Todo '{slug}' not found")
    frontmatter = record.frontmatter.model_copy(
        update={"status": "claimed", "claimed_by": claimed_by, "claimed_at": now_iso()}
    )
    _write_frontmatter(slug, frontmatter)
    _claimed_dir().mkdir(parents=True, exist_ok=True)
    destination = _claimed_path(slug)
    if path != destination:
        path.rename(destination)
    return destination


def delete(slug: str) -> None:
    path = _item_path(slug)
    if not path.exists():
        raise ValueError(f"Todo '{slug}' not found")
    path.unlink()


def resolve(prefix: str) -> tuple[str | None, list[str]]:
    normalized = slugify(prefix)
    if not normalized:
        return None, []

    open_slugs = [
        path.stem
        for path in PROJECT_PATHS.todos_dir.glob("*.md")
        if path.is_file()
    ]
    claimed_slugs = [
        path.stem
        for path in _claimed_dir().glob("*.md")
        if path.is_file()
    ]
    all_slugs = open_slugs + claimed_slugs

    if normalized in all_slugs:
        return normalized, [normalized]

    open_matches = [slug for slug in open_slugs if slug.startswith(normalized)]
    claimed_matches = [slug for slug in claimed_slugs if slug.startswith(normalized)]
    matches = sorted(open_matches + claimed_matches)

    if len(matches) == 1:
        return matches[0], matches
    if len(open_matches) == 1 and len(matches) > 1:
        return open_matches[0], matches
    return None, matches
