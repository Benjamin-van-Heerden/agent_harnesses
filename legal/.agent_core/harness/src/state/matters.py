import shutil
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
from src.utils.markdown import MarkdownDocument, frontmatter_get, frontmatter_set, write_markdown


def parse_matter_status(path: Path) -> MatterStatus:
    matter_dir = path.parent.parent
    return MatterStatus(
        matter_type=frontmatter_get(path, "matter_type"),
        status=frontmatter_get(path, "status"),
        priority=frontmatter_get(path, "priority"),
        opened=frontmatter_get(path, "opened"),
        client=frontmatter_get(path, "client"),
        billing=frontmatter_get(path, "billing"),
        next_obligation=frontmatter_get(path, "next_obligation"),
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


def find_matters(pattern: str, paths: ProjectPaths = PROJECT_PATHS) -> list[Path]:
    if not paths.clients_root.is_dir():
        return []
    matches: list[Path] = []
    for client in sorted(path for path in paths.clients_root.iterdir() if path.is_dir()):
        for bucket in ("open", "resolved"):
            bucket_dir = client / "matters" / bucket
            if not bucket_dir.is_dir():
                continue
            for matter_dir in sorted(path for path in bucket_dir.iterdir() if path.is_dir()):
                if pattern in matter_dir.name:
                    matches.append(matter_dir)
    return matches


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
        options = ", ".join(str(path.relative_to(paths.project_root)) for path in matches)
        raise ValueError(f"multiple matters match '{input_ref}': {options}")
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
            summary=f"{matter_type} — {matter_slug} (priority {priority}, {billing})",
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
    shutil.move(str(matter_dir), str(destination))
    return destination
