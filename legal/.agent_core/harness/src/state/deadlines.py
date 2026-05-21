import re
from datetime import datetime, timedelta
from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.state.matters import resolve_matter
from src.state.models import ChronologyEntry, DeadlineEntry
from src.state.records import append_record
from src.state.templates import ensure_file_from_template
from src.state.time import today
from src.state.validation import validate_date
from src.utils.markdown import frontmatter_set


DEADLINE_LINE_RE = re.compile(r"^- \[([a-z_]+)\] (\d{4}-\d{2}-\d{2}) - ([^-]+) - (.+)$")
LEGACY_DEADLINE_LINE_RE = re.compile(r"^- \[([a-z_]+)\] (\d{4}-\d{2}-\d{2}) — ([^—]+) — (.+)$")


def parse_deadline_line(line: str) -> DeadlineEntry | None:
    match = DEADLINE_LINE_RE.match(line) or LEGACY_DEADLINE_LINE_RE.match(line)
    if match is None:
        return None
    return DeadlineEntry(
        status=match.group(1),
        due_date=match.group(2),
        category=match.group(3).strip(),
        description=match.group(4).strip(),
    )


def read_deadlines(path: Path) -> list[DeadlineEntry]:
    if not path.is_file():
        return []
    entries: list[DeadlineEntry] = []
    for line in path.read_text().splitlines():
        entry = parse_deadline_line(line)
        if entry is not None:
            entries.append(entry)
    return entries


def update_next_deadline(matter_dir: Path) -> str:
    deadlines = read_deadlines(matter_dir / "info" / "deadlines.md")
    open_dates = [entry.due_date for entry in deadlines if entry.status == "open"]
    next_deadline = min(open_dates) if open_dates else "null"
    frontmatter_set(matter_dir / "info" / "status.md", "next_deadline", next_deadline)
    return next_deadline


def add_deadline(matter_ref: str, due_date: str, category: str, description: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_date(due_date)
    matter_dir = resolve_matter(matter_ref, paths)
    file = matter_dir / "info" / "deadlines.md"
    ensure_file_from_template(file, "deadlines", paths)
    with file.open("a") as handle:
        handle.write(f"- [open] {due_date} — {category} — {description}\n")
    update_next_deadline(matter_dir)
    append_record(
        matter_dir,
        ChronologyEntry(date=today(), kind="deadline:added", summary=f"{due_date} — {category} — {description}"),
    )
    return file


def upcoming_deadlines(days: int = 14, paths: ProjectPaths = PROJECT_PATHS) -> list[tuple[str, Path, DeadlineEntry]]:
    today_date = today()
    cutoff = (datetime.strptime(today_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
    rows: list[tuple[str, Path, DeadlineEntry]] = []
    for file in sorted(paths.clients_root.glob("*/matters/open/*/info/deadlines.md")):
        matter_dir = file.parent.parent
        for entry in read_deadlines(file):
            if entry.status == "open" and today_date <= entry.due_date <= cutoff:
                rows.append((entry.due_date, matter_dir, entry))
    return sorted(rows, key=lambda row: (row[0], str(row[1])))
