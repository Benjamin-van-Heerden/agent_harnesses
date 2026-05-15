from __future__ import annotations

import subprocess
import tomllib
from datetime import datetime
from typing import Any

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import create_log_frontmatter
from src.utils.markdown import read_markdown, slugify, write_markdown


DEFAULT_TEMPLATE = """# Work Log - {short title}

## Overarching Goals

{goals}

## What Was Accomplished

{work}

## Key Files Affected

{files}

## What Comes Next

{next}
"""


def _git_user_name() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            cwd=PROJECT_PATHS.project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _current_username() -> str:
    git_name = _git_user_name()
    mappings_file = PROJECT_PATHS.user_mappings_file
    if mappings_file.exists():
        try:
            with open(mappings_file, "rb") as f:
                mappings = tomllib.load(f)
            for username, details in mappings.items():
                if isinstance(details, dict) and details.get("name") == git_name:
                    return slugify(username)
        except Exception:
            pass
    return slugify(git_name)


def _filename(created_at: datetime, username: str) -> str:
    return f"{username}_{created_at.strftime('%Y%m%d')}_{created_at.strftime('%H%M%S')}_session.md"


def _parse_filename(filename: str) -> tuple[str, datetime] | None:
    if not filename.endswith("_session.md"):
        return None

    base = filename.replace("_session.md", "")
    parts = base.rsplit("_", 2)
    if len(parts) == 3:
        try:
            return parts[0], datetime.strptime(f"{parts[1]}_{parts[2]}", "%Y%m%d_%H%M%S")
        except ValueError:
            return None
    return None


def _to_record(
    username: str,
    created_at: datetime,
    metadata: dict[str, Any],
    body: str,
    filename: str,
) -> dict[str, Any]:
    return {
        "username": username,
        "created_at": created_at.isoformat(),
        "date": created_at.date().isoformat(),
        "filename": filename,
        "body": body,
        **metadata,
    }


def create(spec_slug: str | None = None):
    PROJECT_PATHS.logs_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now()
    username = _current_username()
    path = PROJECT_PATHS.logs_dir / _filename(created_at, username)
    metadata = create_log_frontmatter(created_at, username, spec_slug)
    write_markdown(path, metadata.to_dict(), DEFAULT_TEMPLATE)
    return path


def get(filename: str) -> dict[str, Any] | None:
    path = PROJECT_PATHS.logs_dir / filename
    parsed = _parse_filename(filename)
    if parsed is None or not path.exists():
        return None
    username, created_at = parsed
    metadata, body = read_markdown(path)
    return _to_record(username, created_at, metadata, body, filename)


def list_all(
    limit: int = 10,
    spec_slug: str | None = None,
    username: str | None = None,
) -> list[dict[str, Any]]:
    if not PROJECT_PATHS.logs_dir.exists():
        return []

    records = []
    for path in PROJECT_PATHS.logs_dir.iterdir():
        if not path.is_file():
            continue
        parsed = _parse_filename(path.name)
        if parsed is None:
            continue
        file_username, created_at = parsed
        metadata, body = read_markdown(path)
        if spec_slug is not None and metadata.get("spec_slug") != spec_slug:
            continue
        if username is not None and file_username != username:
            continue
        records.append(_to_record(file_username, created_at, metadata, body, path.name))

    records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return records[:limit]
