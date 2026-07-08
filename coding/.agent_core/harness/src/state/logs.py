from datetime import datetime
from pathlib import Path

from src.config.paths import PROJECT_PATHS
from src.models.frontmatter import LogFrontmatter, create_log_frontmatter
from src.state.models import WorkLog
from src.state.user_mappings import current_username
from src.utils.markdown import read_markdown, write_markdown

DEFAULT_TEMPLATE = """Work Log - {short title}

## Overarching Goals

{
Broad goals and what we were trying to achieve with this work in the context of our interaction so far.
}

## What Was Accomplished

{
Description of what was done. Use appropriate subtitles to organize work done and things achieved.

Don't mention anything that is not relevant to actual changes made, e.g. deliberations or context building actions. You can be technical here and use actual code snippets and examples.
}

## Key Files Affected

{
List of files affected and changes made. Be reasonably detailed here
}

## Errors and Barriers

{
Implementation errors and barriers encountered that have not been resolved yet. Mention approaches which were tried and failed so we can learn from them and avoid repeating mistakes.

(Omit this entire section if there were no errors or barriers)
}

## What Comes Next

{
If there are next steps or logical progressions from where we were, mention/list them here.

Be explicit about work done and expectations for follow up sessions. Remember that future sessions won't have any context about what was discussed.

If we were on an active spec, mention which parts of the spec were completed and which parts need further work.

Do not mention "obvious things" here such as harness commands that need to be ran or tasks that still need completion.

(This section may also be omitted entirely if nothing major needs to happen or if the user doesn't specify things they want for future sessions)
}
"""


def _filename(created_at: datetime, username: str) -> str:
    return f"{username}_{created_at.strftime('%Y%m%d')}_{created_at.strftime('%H%M%S')}_session.md"


def _parse_filename(filename: str) -> tuple[str, datetime] | None:
    if not filename.endswith("_session.md"):
        return None

    base = filename.replace("_session.md", "")
    parts = base.rsplit("_", 2)
    if len(parts) == 3:
        try:
            return parts[0], datetime.strptime(
                f"{parts[1]}_{parts[2]}", "%Y%m%d_%H%M%S"
            )
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
    username = current_username()
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
