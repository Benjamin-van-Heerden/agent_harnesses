from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.state.matters import resolve_matter
from src.state.models import WorkLogRecord
from src.state.templates import render_template
from src.state.time import now_stamp, now_time, today
from src.utils.markdown import read_markdown


def parse_work_log(path: Path) -> WorkLogRecord:
    document = read_markdown(path)
    return WorkLogRecord(
        date=document.frontmatter.get("date", ""),
        session_start=document.frontmatter.get("session_start", ""),
        matter=document.frontmatter.get("matter", "null"),
        path=path,
    )


def create_work_log(matter_ref: str = "", paths: ProjectPaths = PROJECT_PATHS) -> Path:
    matter_path = "null"
    if matter_ref:
        matter_dir = resolve_matter(matter_ref, paths)
        matter_path = str(matter_dir.relative_to(paths.project_root))

    path = paths.logs_root / f"{now_stamp()}_log.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_template(
            "log",
            paths,
            TODAY=today(),
            TIME=now_time(),
            MATTER_REF=matter_path,
        )
    )
    return path


def recent_work_logs(limit: int = 5, paths: ProjectPaths = PROJECT_PATHS) -> list[WorkLogRecord]:
    if not paths.logs_root.is_dir():
        return []
    return [parse_work_log(path) for path in sorted(paths.logs_root.glob("*.md"), reverse=True)[:limit]]
