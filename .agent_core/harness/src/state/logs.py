import subprocess
import tomllib
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import LogFrontmatter, create_log_frontmatter
from src.state.models import WorkLog
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


class UserMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    email: str | None = None


USER_MAPPINGS_ADAPTER = TypeAdapter(dict[str, UserMapping])


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
                mappings = USER_MAPPINGS_ADAPTER.validate_python(tomllib.load(f))
            for username, details in mappings.items():
                if details.name == git_name:
                    return slugify(username)
        except Exception:
            pass
    return slugify(git_name)


def current_username() -> str:
    return _current_username()


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
    metadata: object,
    body: str,
    filename: str,
) -> WorkLog:
    frontmatter = LogFrontmatter.model_validate(metadata)
    return WorkLog(
        username=username,
        created_at=created_at.isoformat(),
        date=created_at.date().isoformat(),
        filename=filename,
        body=body,
        frontmatter=frontmatter,
    )


def create(spec_slug: str | None = None) -> Path:
    PROJECT_PATHS.logs_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now()
    username = _current_username()
    path = PROJECT_PATHS.logs_dir / _filename(created_at, username)
    metadata = create_log_frontmatter(created_at, username, spec_slug)
    write_markdown(path, metadata.to_dict(), DEFAULT_TEMPLATE)
    return path


def get(filename: str) -> WorkLog | None:
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
) -> list[WorkLog]:
    if not PROJECT_PATHS.logs_dir.exists():
        return []

    records: list[WorkLog] = []
    for path in PROJECT_PATHS.logs_dir.iterdir():
        if not path.is_file():
            continue
        parsed = _parse_filename(path.name)
        if parsed is None:
            continue
        file_username, created_at = parsed
        metadata, body = read_markdown(path)
        record = _to_record(file_username, created_at, metadata, body, path.name)
        if spec_slug is not None and record.spec_slug != spec_slug:
            continue
        if username is not None and file_username != username:
            continue
        records.append(record)

    records.sort(key=lambda item: item.created_at, reverse=True)
    return records[:limit]
