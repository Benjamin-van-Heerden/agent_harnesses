from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.models.frontmatter import WorkLogFrontmatter
from src.state.matters import resolve_matter, touch_matter
from src.state.models import WorkLogRecord
from src.state.templates import render_template
from src.state.time import now_stamp, now_time, today
from src.utils.markdown import MarkdownDocument, frontmatter_get, read_markdown, write_markdown


EMPTY_LOG_MARKERS = (
    "## What was done\n_TODO_",
    "## What's next\n_TODO_",
    "## Notes\n_TODO_",
)


def parse_work_log(path: Path) -> WorkLogRecord:
    return WorkLogRecord(
        date=frontmatter_get(path, "date"),
        session_start=frontmatter_get(path, "session_start"),
        matter=frontmatter_get(path, "matter") or "null",
        path=path,
    )


def create_work_log(matter_ref: str = "", paths: ProjectPaths = PROJECT_PATHS) -> Path:
    matter_path: str | None = None
    if matter_ref:
        matter_dir = resolve_matter(matter_ref, paths)
        matter_path = str(matter_dir.relative_to(paths.project_root))
        touch_matter(matter_dir)

    stamp = now_stamp()
    path = paths.logs_root / f"{stamp}_log.md"
    suffix = 1
    while path.exists():
        path = paths.logs_root / f"{stamp}_{suffix}_log.md"
        suffix += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    body = render_template("log", paths, TODAY=today())
    write_markdown(
        path,
        MarkdownDocument(
            frontmatter=WorkLogFrontmatter(
                date=today(),
                session_start=now_time(),
                matter=matter_path,
            ).to_dict(),
            body=body,
        ),
    )
    return path


def is_empty_work_log(path: Path) -> bool:
    if not path.is_file():
        return False
    document = read_markdown(path)
    return all(marker in document.body for marker in EMPTY_LOG_MARKERS)


def cleanup_empty_work_logs(paths: ProjectPaths = PROJECT_PATHS) -> list[Path]:
    if not paths.logs_root.is_dir():
        return []
    removed: list[Path] = []
    for path in sorted(paths.logs_root.glob("*.md")):
        if is_empty_work_log(path):
            path.unlink()
            removed.append(path)
    return removed


def recent_work_logs(limit: int = 5, paths: ProjectPaths = PROJECT_PATHS) -> list[WorkLogRecord]:
    if not paths.logs_root.is_dir():
        return []
    return [parse_work_log(path) for path in sorted(paths.logs_root.glob("*.md"), reverse=True)[:limit]]
