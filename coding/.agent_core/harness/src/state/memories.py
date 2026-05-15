from __future__ import annotations

from typing import Any

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import create_memory_frontmatter, now_iso
from src.utils.markdown import read_markdown, slugify, write_markdown


def _item_path(slug: str):
    return PROJECT_PATHS.memories_dir / f"{slug}.md"


def _to_record(slug: str, metadata: dict[str, Any], body: str) -> dict[str, Any]:
    return {"slug": slug, "body": body, **metadata}


def create(title: str, content: str = ""):
    slug = slugify(title)
    path = _item_path(slug)
    if path.exists():
        raise ValueError(f"Memory '{slug}' already exists")
    metadata = create_memory_frontmatter(title)
    write_markdown(path, metadata.to_dict(), content)
    return path


def get(slug: str) -> dict[str, Any] | None:
    path = _item_path(slug)
    if not path.exists():
        return None
    metadata, body = read_markdown(path)
    return _to_record(slug, metadata, body)


def list_all() -> list[dict[str, Any]]:
    if not PROJECT_PATHS.memories_dir.exists():
        return []

    records = []
    for path in PROJECT_PATHS.memories_dir.iterdir():
        if path.is_file() and path.suffix == ".md":
            metadata, body = read_markdown(path)
            records.append(_to_record(path.stem, metadata, body))

    records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return records


def update(slug: str, content: str) -> None:
    path = _item_path(slug)
    if not path.exists():
        raise ValueError(f"Memory '{slug}' not found")
    metadata, _ = read_markdown(path)
    metadata["updated_at"] = now_iso()
    write_markdown(path, metadata, content)


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
        item["slug"]
        for item in list_all()
        if item.get("title", "").lower() == identifier.lower()
        or item["slug"].startswith(normalized)
    ]
    if len(matches) == 1:
        return matches[0]
    return None
