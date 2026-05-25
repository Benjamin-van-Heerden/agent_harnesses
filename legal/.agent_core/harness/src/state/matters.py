import shutil
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import cast

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.models.frontmatter import MatterStatusFrontmatter, Priority
from src.state.clients import resolve_client
from src.state.chronology import write_chronology_event
from src.state.models import ChronologyEntry, MatterRef, MatterStatus
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_priority, validate_slug
from src.utils.markdown import MarkdownDocument, frontmatter_get, frontmatter_set, read_markdown, write_markdown


def _optional_text(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item)]


def _metadata(path: Path) -> Mapping[str, object]:
    return read_markdown(path).frontmatter


def touch_matter(matter_dir: Path) -> None:
    status_file = matter_dir / "info" / "status.md"
    if not status_file.is_file():
        raise FileNotFoundError(f"no info/status.md in {matter_dir}")
    document = read_markdown(status_file)
    metadata = dict(document.frontmatter)
    metadata["last_touched_at"] = datetime.now().isoformat(timespec="seconds")
    write_markdown(status_file, MarkdownDocument(frontmatter=metadata, body=document.body))


def parse_matter_status(path: Path) -> MatterStatus:
    matter_dir = path.parent.parent
    metadata = _metadata(path)
    return MatterStatus(
        matter_type=str(metadata.get("matter_type", "")),
        status=str(metadata.get("status", "")),
        priority=str(metadata.get("priority", "")),
        opened=str(metadata.get("opened", "")),
        client=str(metadata.get("client", "")),
        billing=str(metadata.get("billing", "")),
        case_number=_optional_text(metadata.get("case_number")),
        physical_files=_string_list(metadata.get("physical_files")),
        workflow=_optional_text(metadata.get("workflow")),
        last_touched_at=_optional_text(metadata.get("last_touched_at")),
        next_obligation=frontmatter_get(path, "next_obligation"),
        tags=_string_list(metadata.get("tags")),
        path=path,
        matter_dir=matter_dir,
    )


def matter_ref_from_dir(matter_dir: Path) -> MatterRef:
    status_file = matter_dir / "info" / "status.md"
    client_slug = matter_dir.parent.parent.parent.name
    return MatterRef(
        client_slug=client_slug,
        matter_slug=matter_dir.name,
        matter_dir=matter_dir,
        status_file=status_file,
        is_resolved=matter_dir.parent.name == "resolved",
    )


def list_open_matters(paths: ProjectPaths = PROJECT_PATHS) -> list[MatterStatus]:
    if not paths.clients_root.is_dir():
        return []
    return [
        parse_matter_status(path)
        for path in sorted(paths.clients_root.glob("*/matters/open/*/info/status.md"))
    ]


def all_matter_statuses(paths: ProjectPaths = PROJECT_PATHS) -> list[MatterStatus]:
    if not paths.clients_root.is_dir():
        return []
    return [
        parse_matter_status(path)
        for path in sorted(paths.clients_root.glob("*/matters/*/*/info/status.md"))
    ]


def _client_display_name(client_slug: str, paths: ProjectPaths) -> str:
    profile = paths.clients_root / client_slug / "profile.md"
    return frontmatter_get(profile, "display_name")


def _search_values(matter: MatterStatus, paths: ProjectPaths) -> list[str]:
    return [
        matter.matter_dir.name,
        matter.client,
        _client_display_name(matter.client, paths),
        matter.matter_type,
        matter.status,
        matter.case_number or "",
        *(matter.physical_files),
        *(matter.tags),
        matter.workflow or "",
    ]


def find_matters(pattern: str, paths: ProjectPaths = PROJECT_PATHS) -> list[Path]:
    query = pattern.casefold().strip()
    if not query:
        return []
    return [
        matter.matter_dir
        for matter in all_matter_statuses(paths)
        if any(query in value.casefold() for value in _search_values(matter, paths))
    ]


def ambiguous_matter_message(input_ref: str, matches: list[Path], paths: ProjectPaths) -> str:
    options = "\n".join(f"- {path.relative_to(paths.project_root)}" for path in matches)
    return (
        f"multiple matters match '{input_ref}'. Ask the lawyer which matter to use, then rerun the command with a more specific identifier.\n{options}"
    )


def resolve_matter(input_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    candidate = paths.project_root / input_ref
    if candidate.is_dir() and (candidate / "info" / "status.md").is_file():
        return candidate

    raw_candidate = Path(input_ref)
    if raw_candidate.is_dir() and (raw_candidate / "info" / "status.md").is_file():
        return raw_candidate.resolve()

    matches = find_matters(input_ref, paths)

    if not matches:
        raise FileNotFoundError(f"no matter found matching '{input_ref}'")
    if len(matches) > 1:
        raise ValueError(ambiguous_matter_message(input_ref, matches, paths))
    return matches[0]


def list_unparsed_files(matter_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> list[Path]:
    matter_dir = resolve_matter(matter_ref, paths)
    raw_dir = matter_dir / "raw"
    reference_dir = matter_dir / "reference"
    if not raw_dir.is_dir():
        return []

    reference_stems = {path.stem for path in reference_dir.iterdir() if path.is_file()} if reference_dir.is_dir() else set()
    return [
        path
        for path in sorted(raw_dir.iterdir())
        if path.is_file() and path.stem not in reference_stems
    ]


def create_matter(
    client_slug: str,
    matter_type: str,
    matter_slug: str,
    priority: str = "normal",
    billing: str = "hourly",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    validate_slug(client_slug)
    validate_slug(matter_type)
    validate_slug(matter_slug)
    validate_priority(priority)

    client_path = resolve_client(client_slug, paths)
    directory_name = f"{datetime.now().strftime('%Y%m%d')}-{matter_type}-{matter_slug}"
    matter_dir = client_path / "matters" / "open" / directory_name
    if matter_dir.exists():
        raise FileExistsError(f"matter already exists: {matter_dir}")

    (matter_dir / "info" / "chronology").mkdir(parents=True, exist_ok=True)
    (matter_dir / "info" / "obligations").mkdir(parents=True, exist_ok=True)
    (matter_dir / "info" / "todos").mkdir(parents=True, exist_ok=True)
    (matter_dir / "raw").mkdir(parents=True, exist_ok=True)
    (matter_dir / "reference").mkdir(parents=True, exist_ok=True)

    status_body = render_template("status", paths)
    write_markdown(
        matter_dir / "info" / "status.md",
        MarkdownDocument(
            frontmatter=MatterStatusFrontmatter(
                matter_type=matter_type,
                priority=cast(Priority, priority),
                opened=today(),
                client=client_slug,
                billing=billing,
            ).to_dict(),
            body=status_body,
        ),
    )
    write_chronology_event(
        matter_dir,
        ChronologyEntry(
            date=today(),
            kind="matter_opened",
            summary=f"{matter_type} - {matter_slug} (priority {priority}, {billing})",
        ),
    )
    return matter_dir


def resolve_open_matter(input_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    matter_dir = resolve_matter(input_ref, paths)
    if matter_dir.parent.name != "open":
        raise ValueError(f"matter is not under matters/open/: {matter_dir}")
    return matter_dir


def close_matter(input_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    matter_dir = resolve_open_matter(input_ref, paths)
    status_file = matter_dir / "info" / "status.md"
    if not status_file.is_file():
        raise FileNotFoundError(f"no info/status.md in {matter_dir}")
    if frontmatter_get(status_file, "status") == "resolved":
        raise ValueError("matter already resolved")

    destination = matter_dir.parent.parent / "resolved" / matter_dir.name
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    frontmatter_set(status_file, "status", "resolved")
    write_chronology_event(matter_dir, ChronologyEntry(date=today(), kind="matter_resolved", summary="Matter closed."))
    touch_matter(matter_dir)
    shutil.move(str(matter_dir), str(destination))
    return destination
