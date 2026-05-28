import tomllib
from datetime import datetime
from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, matter_chronology_file
from src.state.models import ChronologyEntry
from src.state.validation import validate_date


VALID_CHRONOLOGY_KINDS = (
    "conversation",
    "meeting",
    "email",
    "letter",
    "filing",
    "service",
    "note",
)
CHRONOLOGY_HEADER = "# Matter chronology. Add entries through the legal harness.\n"


def _toml_string(value: str) -> str:
    return (
        '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    )


def validate_chronology_kind(value: str) -> None:
    if value in VALID_CHRONOLOGY_KINDS:
        return
    raise ValueError(f"invalid chronology kind '{value}'")


def write_chronology_event(matter_dir: Path, entry: ChronologyEntry) -> Path:
    validate_date(entry.date)
    validate_chronology_kind(entry.kind)
    path = matter_chronology_file(matter_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text() if path.is_file() else CHRONOLOGY_HEADER
    if existing and not existing.endswith("\n"):
        existing += "\n"
    event = "\n".join(
        [
            "[[events]]",
            f"date = {_toml_string(entry.date)}",
            f"kind = {_toml_string(entry.kind)}",
            f"summary = {_toml_string(entry.summary)}",
            f"body = {_toml_string(entry.body)}",
            f"created_at = {_toml_string(datetime.now().isoformat(timespec='seconds'))}",
            "",
        ]
    )
    path.write_text(existing + event)
    return path


def add_chronology_event(
    matter_ref: str,
    date: str,
    kind: str,
    summary: str,
    body: str = "",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    from src.state.matters import resolve_matter, touch_matter

    if not summary:
        raise ValueError("summary must not be empty")
    matter_dir = resolve_matter(matter_ref, paths)
    event = write_chronology_event(
        matter_dir, ChronologyEntry(date=date, kind=kind, summary=summary, body=body)
    )
    touch_matter(matter_dir)
    return event


def list_chronology(
    matter_ref: str, paths: ProjectPaths = PROJECT_PATHS
) -> list[ChronologyEntry]:
    from src.state.matters import resolve_matter

    matter_dir = resolve_matter(matter_ref, paths)
    entries: list[ChronologyEntry] = []
    path = matter_chronology_file(matter_dir)
    if path.is_file():
        data = tomllib.loads(path.read_text())
        raw_events = data.get("events", [])
        if isinstance(raw_events, list):
            for event in raw_events:
                if not isinstance(event, dict):
                    continue
                entries.append(
                    ChronologyEntry(
                        date=str(event.get("date", "")),
                        kind=str(event.get("kind", "")),
                        summary=str(event.get("summary", "")),
                        body=str(event.get("body", "")),
                    )
                )
    legacy_dir = matter_dir / "info" / "chronology"
    if legacy_dir.is_dir():
        for legacy_path in sorted(legacy_dir.glob("*/*.toml")):
            data = tomllib.loads(legacy_path.read_text())
            entries.append(
                ChronologyEntry(
                    date=str(data.get("date", "")),
                    kind=str(data.get("kind", "")),
                    summary=str(data.get("summary", "")),
                    body=str(data.get("body", "")),
                )
            )
    return sorted(entries, key=lambda entry: (entry.date, entry.kind, entry.summary))


def ensure_chronology_file(matter_dir: Path) -> Path:
    path = matter_chronology_file(matter_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(CHRONOLOGY_HEADER)
    return path
