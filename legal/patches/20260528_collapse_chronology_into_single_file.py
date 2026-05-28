import shutil
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast


CHRONOLOGY_HEADER = "# Matter chronology. Add entries through the legal harness.\n"
BASE_FIELDS = ("date", "kind", "summary", "body", "created_at", "source_path")
VALID_KINDS = {
    "conversation",
    "meeting",
    "email",
    "letter",
    "filing",
    "service",
    "note",
}


def _toml_string(value: str) -> str:
    return (
        '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    )


def _toml_value(value: object) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return _toml_string(value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        items = cast("list[str]", value)
        return "[" + ", ".join(_toml_string(item) for item in items) + "]"
    return None


def _legacy_chronology_dirs(project_root: Path) -> list[Path]:
    roots = [project_root / "ZZ_CLIENTS", project_root / "UNBOUND"]
    dirs: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        dirs.extend(path for path in root.rglob("info/chronology") if path.is_dir())
    return sorted(dirs)


def needs_patch(project_root: Path) -> bool:
    return any(
        list(path.glob("*/*.toml")) for path in _legacy_chronology_dirs(project_root)
    )


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with open(path, "rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _existing_source_paths(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = _read_toml(path)
    raw_events = data.get("events", [])
    if not isinstance(raw_events, list):
        return set()
    source_paths: set[str] = set()
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            continue
        source_path = raw_event.get("source_path")
        if isinstance(source_path, str) and source_path:
            source_paths.add(source_path)
    return source_paths


def _event_from_legacy_file(matter_root: Path, legacy_path: Path) -> dict[str, object]:
    data = _read_toml(legacy_path)
    kind = str(data.get("kind") or legacy_path.parent.name)
    if kind not in VALID_KINDS:
        kind = "note"
    source_path = legacy_path.relative_to(matter_root).as_posix()
    created_at = data.get("created_at")
    if not isinstance(created_at, str) or not created_at:
        created_at = (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
    event: dict[str, object] = {
        "date": str(data.get("date", "")),
        "kind": kind,
        "summary": str(data.get("summary", legacy_path.stem)),
        "body": str(data.get("body", "")),
        "created_at": created_at,
        "source_path": source_path,
    }
    for key, value in sorted(data.items()):
        if key in BASE_FIELDS:
            continue
        if _toml_value(value) is not None:
            event[f"legacy_{key}"] = value
    return event


def _append_events(path: Path, events: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text() if path.is_file() else CHRONOLOGY_HEADER
    if existing and not existing.endswith("\n"):
        existing += "\n"
    lines = [existing.rstrip(), ""]
    for event in events:
        lines.append("[[events]]")
        for key, value in event.items():
            rendered = _toml_value(value)
            if rendered is None:
                continue
            lines.append(f"{key} = {rendered}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n")


def _unique_legacy_destination(info_dir: Path) -> Path:
    base = info_dir / "legacy_chronology"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = info_dir / f"legacy_chronology_{index}"
        if not candidate.exists():
            return candidate
        index += 1


def _collapse_dir(project_root: Path, chronology_dir: Path) -> dict[str, object]:
    info_dir = chronology_dir.parent
    matter_root = info_dir.parent
    chronology_file = info_dir / "chronology.toml"
    existing_sources = _existing_source_paths(chronology_file)
    events: list[dict[str, object]] = []
    for legacy_path in sorted(chronology_dir.glob("*/*.toml")):
        source_path = legacy_path.relative_to(matter_root).as_posix()
        if source_path in existing_sources:
            continue
        events.append(_event_from_legacy_file(matter_root, legacy_path))
    if events:
        _append_events(chronology_file, events)
    destination = _unique_legacy_destination(info_dir)
    shutil.move(str(chronology_dir), str(destination))
    return {
        "matter": matter_root.relative_to(project_root).as_posix(),
        "events": len(events),
        "legacy_dir": destination.name,
    }


def run(project_root: Path) -> dict[str, object]:
    details = [
        _collapse_dir(project_root, path)
        for path in _legacy_chronology_dirs(project_root)
        if list(path.glob("*/*.toml"))
    ]
    return {"changed": bool(details), "details": details}
