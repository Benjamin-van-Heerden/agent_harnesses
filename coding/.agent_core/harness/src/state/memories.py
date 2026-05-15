from __future__ import annotations

from pathlib import Path

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import MemoryFrontmatter, create_memory_frontmatter, now_iso
from src.state.models import Memory
from src.utils.markdown import read_markdown, slugify, write_markdown


def _item_path(slug: str) -> Path:
    return PROJECT_PATHS.memories_dir / f"{slug}.md"


def _to_memory(slug: str, metadata: object, body: str) -> Memory:
    frontmatter = MemoryFrontmatter.model_validate(metadata)
    return Memory(slug=slug, body=body, frontmatter=frontmatter)


def create(title: str, content: str = "") -> Path:
    slug = slugify(title)
    path = _item_path(slug)
    if path.exists():
        raise ValueError(f"Memory '{slug}' already exists")
    metadata = create_memory_frontmatter(title)
    write_markdown(path, metadata.to_dict(), content)
    return path


def get(slug: str) -> Memory | None:
    path = _item_path(slug)
    if not path.exists():
        return None
    metadata, body = read_markdown(path)
    return _to_memory(slug, metadata, body)


def list_all() -> list[Memory]:
    if not PROJECT_PATHS.memories_dir.exists():
        return []

    records: list[Memory] = []
    for path in PROJECT_PATHS.memories_dir.iterdir():
        if path.is_file() and path.suffix == ".md":
            metadata, body = read_markdown(path)
            records.append(_to_memory(path.stem, metadata, body))

    records.sort(key=lambda item: item.created_at, reverse=True)
    return records


def update(slug: str, content: str) -> None:
    path = _item_path(slug)
    if not path.exists():
        raise ValueError(f"Memory '{slug}' not found")
    metadata, _ = read_markdown(path)
    frontmatter = MemoryFrontmatter.model_validate(metadata).model_copy(
        update={"updated_at": now_iso()}
    )
    write_markdown(path, frontmatter.to_dict(), content)


def delete(slug: str) -> None:
    path = _item_path(slug)
    if not path.exists():
        raise ValueError(f"Memory '{slug}' not found")
    path.unlink()


def resolve(identifier: str) -> str | None:
    normalized = slugify(identifier)
    if get(normalized):
        return normalized

    matches = [
        item.slug
        for item in list_all()
        if item.title.lower() == identifier.lower()
        or item.slug.startswith(normalized)
    ]
    if len(matches) == 1:
        return matches[0]
    return None
