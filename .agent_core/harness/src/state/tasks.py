from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import create_task_frontmatter, now_iso
from src.state import specs
from src.utils.markdown import read_markdown, slugify, write_markdown


def _tasks_dir(spec_slug: str):
    return PROJECT_PATHS.specs_dir / spec_slug / "tasks"


def _next_order(spec_slug: str) -> int:
    existing = []
    for path in _tasks_dir(spec_slug).glob("*.md"):
        match = re.match(r"^(\d+)_", path.name)
        if match:
            existing.append(int(match.group(1)))
    return max(existing, default=0) + 1


def _task_path(spec_slug: str, slug: str):
    for path in _tasks_dir(spec_slug).glob(f"*_{slug}.md"):
        return path
    return None


def _to_record(slug: str, path: Path, metadata: dict[str, Any], body: str) -> dict[str, Any]:
    return {"slug": slug, "filename": path.name, "body": body, **metadata}


def _order_prefix(path: Path) -> str:
    match = re.match(r"^(\d+)_", path.name)
    if match:
        return match.group(1)
    return "00"


def create(spec_slug: str, title: str, description: str = ""):
    if specs.get(spec_slug) is None:
        raise ValueError(f"Spec '{spec_slug}' not found")

    slug = slugify(title)
    if _task_path(spec_slug, slug) is not None:
        raise ValueError(f"Task '{slug}' already exists")

    order = _next_order(spec_slug)
    path = _tasks_dir(spec_slug) / f"{order:02d}_{slug}.md"
    metadata = create_task_frontmatter(title)
    write_markdown(path, metadata.to_dict(), description)
    return path


def get(spec_slug: str, slug: str) -> dict[str, Any] | None:
    path = _task_path(spec_slug, slug)
    if path is None:
        return None
    metadata, body = read_markdown(path)
    return _to_record(slug, path, metadata, body)


def list_all(spec_slug: str, status: str | None = None) -> list[dict[str, Any]]:
    if not _tasks_dir(spec_slug).exists():
        return []

    records = []
    for path in sorted(_tasks_dir(spec_slug).glob("*.md")):
        slug = re.sub(r"^\d+_", "", path.stem)
        metadata, body = read_markdown(path)
        if status is not None and metadata.get("status") != status:
            continue
        records.append(_to_record(slug, path, metadata, body))
    return records


def complete(spec_slug: str, slug: str, notes: str = "") -> None:
    path = _task_path(spec_slug, slug)
    if path is None:
        raise ValueError(f"Task '{slug}' not found")
    metadata, body = read_markdown(path)
    metadata["status"] = "completed"
    metadata["updated_at"] = now_iso()
    metadata["completed_at"] = metadata["updated_at"]
    if notes:
        body = f"{body.rstrip()}\n\n## Completion Notes\n\n{notes}\n"
    write_markdown(path, metadata, body)


def amend(spec_slug: str, slug: str, notes: str) -> None:
    path = _task_path(spec_slug, slug)
    if path is None:
        raise ValueError(f"Task '{slug}' not found")
    metadata, body = read_markdown(path)
    metadata["status"] = "todo"
    metadata["updated_at"] = now_iso()
    metadata["completed_at"] = None
    body = f"{body.rstrip()}\n\n## Amendment\n\n{notes}\n"
    write_markdown(path, metadata, body)


def rename(spec_slug: str, slug: str, title: str) -> Path:
    path = _task_path(spec_slug, slug)
    if path is None:
        raise ValueError(f"Task '{slug}' not found")

    new_slug = slugify(title)
    existing = _task_path(spec_slug, new_slug)
    if existing is not None and existing != path:
        raise ValueError(f"Task '{new_slug}' already exists")

    metadata, body = read_markdown(path)
    metadata["title"] = title
    metadata["updated_at"] = now_iso()
    new_path = path.parent / f"{_order_prefix(path)}_{new_slug}.md"
    write_markdown(new_path, metadata, body)
    if new_path != path:
        path.unlink()
    return new_path
