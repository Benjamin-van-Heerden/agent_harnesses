from __future__ import annotations

import shutil
from pathlib import Path

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import SpecFrontmatter, SpecStatus, create_spec_frontmatter, now_iso
from src.state.models import Spec
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


def _active_path(slug: str) -> Path:
    return PROJECT_PATHS.specs_dir / slug / "spec.md"


def _completed_path(slug: str) -> Path:
    return PROJECT_PATHS.specs_dir / "completed" / slug / "spec.md"


def _abandoned_path(slug: str) -> Path:
    return PROJECT_PATHS.specs_dir / "abandoned" / slug / "spec.md"


def _candidate_paths(slug: str) -> list[Path]:
    return [_active_path(slug), _completed_path(slug), _abandoned_path(slug)]


def _to_spec(slug: str, path: Path, metadata: object, body: str) -> Spec:
    frontmatter = SpecFrontmatter.model_validate(metadata)
    return Spec(slug=slug, path=path, body=body, frontmatter=frontmatter)


def create(title: str, body: str = DEFAULT_BODY) -> Path:
    slug = slugify(title)
    path = _active_path(slug)
    if any(candidate.exists() for candidate in _candidate_paths(slug)):
        raise ValueError(f"Spec '{slug}' already exists")
    metadata = create_spec_frontmatter(title)
    write_markdown(path, metadata.to_dict(), body)
    return path


def create_with_metadata(title: str, metadata: SpecFrontmatter, body: str = DEFAULT_BODY) -> Path:
    slug = slugify(title)
    path = _active_path(slug)
    if any(candidate.exists() for candidate in _candidate_paths(slug)):
        return path
    write_markdown(path, metadata.to_dict(), body)
    return path


def get(slug: str) -> Spec | None:
    for path in _candidate_paths(slug):
        if path.exists():
            metadata, body = read_markdown(path)
            return _to_spec(slug, path, metadata, body)
    return None


def list_all(status: SpecStatus | None = None) -> list[Spec]:
    records: list[Spec] = []
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
            record = _to_spec(slug, spec_file, metadata, body)
            if status is not None and record.status != status:
                continue
            records.append(record)

    records.sort(key=lambda item: item.created_at, reverse=True)
    return records


def update_status(slug: str, status: SpecStatus) -> Path:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    updated_at = now_iso()
    completed_at = record.frontmatter.completed_at
    if status in {"completed", "abandoned"}:
        completed_at = updated_at
    frontmatter = record.frontmatter.model_copy(
        update={"status": status, "updated_at": updated_at, "completed_at": completed_at}
    )

    target_path = record.path
    if status == "completed":
        target_path = _completed_path(slug)
    elif status == "abandoned":
        target_path = _abandoned_path(slug)

    write_markdown(target_path, frontmatter.to_dict(), record.body)
    if target_path != record.path:
        shutil.rmtree(record.path.parent)
    return target_path


def _write_frontmatter(slug: str, frontmatter: SpecFrontmatter) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    write_markdown(record.path, frontmatter.to_dict(), record.body)


def update_issue(slug: str, issue_id: int, issue_url: str) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    frontmatter = record.frontmatter.model_copy(
        update={"issue_id": issue_id, "issue_url": issue_url, "updated_at": now_iso()}
    )
    _write_frontmatter(slug, frontmatter)


def update_branch(slug: str, branch: str) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    frontmatter = record.frontmatter.model_copy(update={"branch": branch, "updated_at": now_iso()})
    _write_frontmatter(slug, frontmatter)


def update_assignment(slug: str, username: str) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    frontmatter = record.frontmatter.model_copy(
        update={"assigned_to": username, "updated_at": now_iso()}
    )
    _write_frontmatter(slug, frontmatter)


def update_pr(slug: str, pr_url: str) -> None:
    record = get(slug)
    if record is None:
        raise ValueError(f"Spec '{slug}' not found")
    frontmatter = record.frontmatter.model_copy(update={"pr_url": pr_url, "updated_at": now_iso()})
    _write_frontmatter(slug, frontmatter)
