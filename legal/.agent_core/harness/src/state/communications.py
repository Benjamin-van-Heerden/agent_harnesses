from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.state.matters import resolve_matter
from src.state.models import ChronologyEntry
from src.state.records import append_record
from src.state.validation import validate_date, validate_direction


def log_communication(
    matter_ref: str,
    date: str,
    direction: str,
    medium: str,
    counterparty: str,
    subject: str,
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    validate_date(date)
    validate_direction(direction)
    matter_dir = resolve_matter(matter_ref, paths)
    return append_record(
        matter_dir,
        ChronologyEntry(
            date=date,
            kind=f"comm:{direction}:{medium}",
            summary=f"{counterparty} — {subject}",
            body="_TODO: body_",
        ),
    )


def record_note(matter_ref: str, date: str, text: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_date(date)
    if not text:
        raise ValueError("text must not be empty")
    matter_dir = resolve_matter(matter_ref, paths)
    summary, separator, body = text.partition("\n")
    return append_record(matter_dir, ChronologyEntry(date=date, kind="note", summary=summary, body=body if separator else ""))
