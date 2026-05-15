from __future__ import annotations

import shutil
from typing import Any

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import create_spec_frontmatter, now_iso
from src.utils.markdown import read_markdown, slugify, write_markdown


DEFAULT_BODY = """## Overview

{Describe the feature or change}

## Goals

- {Goal 1}
- {Goal 2}

## Technical Approach

{How to implement this}

## Success Criteria

- {Criterion 1}
- {Criterion 2}

## Notes

{Additional context}
"""


def _active_path(slug: str):
    return PROJECT_PATHS.specs_dir / slug / "spec.md"


def _completed_path(slug: str):
    return PROJECT_PATHS.specs_dir / "completed" / slug / "spec.md"


def _abandoned_path(slug: str):
    return PROJECT_PATHS.specs_dir / "abandoned" / slug / "spec.md"


def _candidate_paths(slug: str):
    return [_active_path(slug), _completed_path(slug), _abandoned_path(slug)]


def _to_record(slug: str, path, metadata: dict[str, Any], body: str) -> dict[str, Any]:
    return {"slug": slug, "path": path, "body": body, **metadata}


def create(title: str, body: str = DEFAULT_BODY):
    slug = slugify(title)
    path = _active_path(slug)
    if any(candidate.exists() for candidate in _candidate_paths(slug)):
        raise ValueError(f"Spec '{slug}' already exists")
    metadata = create_spec_frontmatter(title)
    write_markdown(path, metadata.to_dict(), body)
    return path


def create_with_metadata(title: str, metadata: dict[str, Any], body: str = DEFAULT_BODY):
    slug = slugify(title)
    path = _active_path(slug)
    if any(candidate.exists() for candidate in _candidate_paths(slug)):
        return path
    write_markdown(path, metadata, body)
    return path


def get(slug: str) -> dict[str, Any] | None:
    for path in _candidate_paths(slug):
        if path.exists():
            metadata, body = read_markdown(path)
            return _to_record(slug, path, metadata, body)
    return None


def list_all(status: str | None = None) -> list[dict[str, Any]]:
    records = []
    roots = [
        PROJECT_PATHS.specs_dir,
        PROJECT_PATHS.specs_dir / "completed",
        PROJECT_PATHS.specs_dir / "abandoned",
    ]
    for root in roots:
        if not root.exists():
            continue
        for spec_file in root.glob("*/spec.md"):
            slug = spec_file.parent.name
            metadata, body = read_markdown(spec_file)
            if status is not None and metadata.get("status") != status:
                continue
            records.append(_to_record(slug, spec_file, metadata, body))

    records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return records


def update_status(slug: str, status: str):
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    metadata, body = read_markdown(record["path"])
    metadata["status"] = status
    metadata["updated_at"] = now_iso()
    if status in {"completed", "abandoned"}:
        metadata["completed_at"] = metadata["updated_at"]

    target_path = record["path"]
    if status == "completed":
        target_path = _completed_path(slug)
    elif status == "abandoned":
        target_path = _abandoned_path(slug)

    write_markdown(target_path, metadata, body)
    if target_path != record["path"]:
        shutil.rmtree(record["path"].parent)
    return target_path


def update(slug: str, **updates) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    metadata, body = read_markdown(record["path"])
    metadata.update(updates)
    metadata["updated_at"] = now_iso()
    write_markdown(record["path"], metadata, body)


def update_issue(slug: str, issue_id: int, issue_url: str) -> None:
    update(slug, issue_id=issue_id, issue_url=issue_url)


def update_branch(slug: str, branch: str) -> None:
    update(slug, branch=branch)


def update_assignment(slug: str, username: str) -> None:
    update(slug, assigned_to=username)


def update_pr(slug: str, pr_url: str) -> None:
    update(slug, pr_url=pr_url)
