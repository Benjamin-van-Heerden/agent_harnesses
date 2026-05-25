import re
import tomllib
from datetime import datetime
from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, matter_chronology_dir
from src.state.models import ChronologyEntry
from src.state.validation import validate_date


VALID_CHRONOLOGY_KINDS = ("conversation", "meeting", "email", "letter", "filing", "service", "note", "matter_opened", "matter_resolved")


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _slug_part(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "event"


def validate_chronology_kind(value: str) -> None:
    if value in VALID_CHRONOLOGY_KINDS:
        return
    raise ValueError(f"invalid chronology kind '{value}'")


def write_chronology_event(matter_dir: Path, entry: ChronologyEntry) -> Path:
    validate_date(entry.date)
    validate_chronology_kind(entry.kind)
    chronology_dir = matter_chronology_dir(matter_dir) / entry.kind
    chronology_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{stamp}-{_slug_part(entry.summary)[:40]}.toml"
    path = chronology_dir / filename
    suffix = 1
    while path.exists():
        path = chronology_dir / f"{stamp}-{_slug_part(entry.summary)[:40]}-{suffix}.toml"
        suffix += 1
    path.write_text(
        "\n".join(
            [
                f'id = {_toml_string(path.stem)}',
                f'date = {_toml_string(entry.date)}',
                f'kind = {_toml_string(entry.kind)}',
                f'summary = {_toml_string(entry.summary)}',
                f'body = {_toml_string(entry.body)}',
                f'created_at = {_toml_string(datetime.now().isoformat(timespec="seconds"))}',
                "",
            ]
        )
    )
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
    event = write_chronology_event(matter_dir, ChronologyEntry(date=date, kind=kind, summary=summary, body=body))
    touch_matter(matter_dir)
    return event


def list_chronology(matter_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> list[ChronologyEntry]:
    from src.state.matters import resolve_matter

    matter_dir = resolve_matter(matter_ref, paths)
    chronology_dir = matter_chronology_dir(matter_dir)
    if not chronology_dir.is_dir():
        return []
    entries: list[ChronologyEntry] = []
    for path in sorted(chronology_dir.glob("*/*.toml")):
        data = tomllib.loads(path.read_text())
        entries.append(
            ChronologyEntry(
                date=str(data.get("date", "")),
                kind=str(data.get("kind", "")),
                summary=str(data.get("summary", "")),
                body=str(data.get("body", "")),
            )
        )
    return entries
