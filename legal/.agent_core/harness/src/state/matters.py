import shutil
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import cast

from src.config.paths import PROJECT_PATHS, ProjectPaths, client_profile
from src.models.frontmatter import MatterStatusFrontmatter, Priority
from src.state.clients import resolve_client, slugify_text
from src.state.chronology import ensure_chronology_file
from src.state.models import MatterRef, MatterStatus
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_priority, validate_slug
from src.utils.markdown import (
    MarkdownDocument,
    frontmatter_get,
    frontmatter_set,
    read_markdown,
    write_markdown,
)


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
    write_markdown(
        status_file, MarkdownDocument(frontmatter=metadata, body=document.body)
    )


def parse_matter_status(path: Path) -> MatterStatus:
    matter_dir = path.parent.parent
    metadata = _metadata(path)
    workspace = str(metadata.get("workspace", "client") or "client")
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
        workspace=workspace,
        unbound_path=str(metadata.get("unbound_path", "") or ""),
    )


def matter_ref_from_dir(matter_dir: Path) -> MatterRef:
    status_file = matter_dir / "info" / "status.md"
    client_slug = frontmatter_get(status_file, "client")
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


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _unbound_status_files(bucket: Path) -> list[Path]:
    if not bucket.is_dir():
        return []
    return sorted(bucket.glob("**/info/status.md"))


def list_open_unbound_matters(
    paths: ProjectPaths = PROJECT_PATHS,
) -> list[MatterStatus]:
    records = [
        parse_matter_status(path)
        for path in _unbound_status_files(paths.unbound_open_root)
    ]
    if paths.unbound_root.is_dir():
        legacy_files = [
            path
            for path in _unbound_status_files(paths.unbound_root)
            if not _is_under(path, paths.unbound_open_root)
            and not _is_under(path, paths.unbound_closed_root)
        ]
        records.extend(parse_matter_status(path) for path in legacy_files)
    return sorted(records, key=lambda record: str(record.matter_dir))


def list_closed_unbound_matters(
    paths: ProjectPaths = PROJECT_PATHS,
) -> list[MatterStatus]:
    return [
        parse_matter_status(path)
        for path in _unbound_status_files(paths.unbound_closed_root)
    ]


def list_untracked_unbound_bundles(paths: ProjectPaths = PROJECT_PATHS) -> list[Path]:
    if not paths.unbound_root.is_dir():
        return []
    ignored_roots = (paths.unbound_open_root, paths.unbound_closed_root)
    bundles: list[Path] = []
    for directory in sorted(
        path for path in paths.unbound_root.glob("**/*") if path.is_dir()
    ):
        if any(_is_under(directory, root) for root in ignored_roots):
            continue
        if (directory / "info" / "status.md").is_file():
            continue
        has_material = (
            any(directory.glob("*.typ"))
            or (directory / "raw").is_dir()
            or (directory / "reference").is_dir()
        )
        has_child_material = any(
            (child / "info" / "status.md").is_file()
            for child in directory.iterdir()
            if child.is_dir()
        )
        if has_material and not has_child_material:
            bundles.append(directory)
    return bundles


def all_matter_statuses(paths: ProjectPaths = PROJECT_PATHS) -> list[MatterStatus]:
    client_matters = (
        []
        if not paths.clients_root.is_dir()
        else [
            parse_matter_status(path)
            for path in sorted(paths.clients_root.glob("*/matters/*/*/info/status.md"))
        ]
    )
    return (
        client_matters
        + list_open_unbound_matters(paths)
        + list_closed_unbound_matters(paths)
    )


def _client_display_name(client_slug: str, paths: ProjectPaths) -> str:
    if client_slug == "unbound":
        return "Unbound"
    return frontmatter_get(client_profile(client_slug, paths), "display_name")


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
        matter.unbound_path,
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


def ambiguous_matter_message(
    input_ref: str, matches: list[Path], paths: ProjectPaths
) -> str:
    options = "\n".join(f"- {path.relative_to(paths.project_root)}" for path in matches)
    return f"multiple matters match '{input_ref}'. Ask the lawyer which matter to use, then rerun the command with a more specific identifier.\n{options}"


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


def list_unparsed_files(
    matter_ref: str, paths: ProjectPaths = PROJECT_PATHS
) -> list[Path]:
    matter_dir = resolve_matter(matter_ref, paths)
    raw_dir = matter_dir / "raw"
    reference_dir = matter_dir / "reference"
    if not raw_dir.is_dir():
        return []

    reference_stems = (
        {path.stem for path in reference_dir.iterdir() if path.is_file()}
        if reference_dir.is_dir()
        else set()
    )
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

    ensure_chronology_file(matter_dir)
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
    return matter_dir


def _normalise_unbound_parts(value: str) -> list[str]:
    parts = [
        part.strip() for part in value.replace("\\", "/").split("/") if part.strip()
    ]
    if not parts:
        raise ValueError("unbound path must include at least one matter name")
    return parts


def _unbound_parent_part(value: str) -> str:
    slug = slugify_text(value)
    return slug.upper()


def _unbound_path_display(parts: list[str], matter_slug: str) -> str:
    return "/".join([*(_unbound_parent_part(part) for part in parts[:-1]), matter_slug])


def create_unbound_matter(
    unbound_path: str,
    priority: str = "normal",
    billing: str = "hourly",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    validate_priority(priority)
    parts = _normalise_unbound_parts(unbound_path)
    matter_slug = slugify_text(parts[-1])
    parent_parts = [_unbound_parent_part(part) for part in parts[:-1]]
    matter_type = slugify_text(parts[0]) if len(parts) > 1 else "unbound"
    matter_dir = paths.unbound_open_root.joinpath(*parent_parts, matter_slug)
    if matter_dir.exists():
        raise FileExistsError(f"unbound matter already exists: {matter_dir}")

    ensure_chronology_file(matter_dir)
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
                client="unbound",
                workspace="unbound",
                unbound_path=_unbound_path_display(parts, matter_slug),
                billing=billing,
            ).to_dict(),
            body=status_body,
        ),
    )
    return matter_dir


def is_unbound_matter(matter_dir: Path, paths: ProjectPaths = PROJECT_PATHS) -> bool:
    return _is_under(matter_dir.resolve(), paths.unbound_root.resolve())


def is_open_matter(matter_dir: Path, paths: ProjectPaths = PROJECT_PATHS) -> bool:
    if is_unbound_matter(matter_dir, paths):
        return not _is_under(matter_dir.resolve(), paths.unbound_closed_root.resolve())
    return matter_dir.parent.name == "open"


def resolve_open_matter(input_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    matter_dir = resolve_matter(input_ref, paths)
    if not is_open_matter(matter_dir, paths):
        raise ValueError(f"matter is not open: {matter_dir}")
    return matter_dir


def close_matter(input_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    matter_dir = resolve_open_matter(input_ref, paths)
    status_file = matter_dir / "info" / "status.md"
    if not status_file.is_file():
        raise FileNotFoundError(f"no info/status.md in {matter_dir}")
    if frontmatter_get(status_file, "status") == "resolved":
        raise ValueError("matter already resolved")

    if is_unbound_matter(matter_dir, paths):
        try:
            relative_path = matter_dir.relative_to(paths.unbound_open_root)
        except ValueError:
            relative_path = matter_dir.relative_to(paths.unbound_root)
        destination = paths.unbound_closed_root / relative_path
    else:
        destination = matter_dir.parent.parent / "resolved" / matter_dir.name
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    frontmatter_set(status_file, "status", "resolved")
    touch_matter(matter_dir)
    shutil.move(str(matter_dir), str(destination))
    return destination


def bind_unbound_matter(
    unbound_ref: str,
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
    source = resolve_open_matter(unbound_ref, paths)
    if not is_unbound_matter(source, paths):
        raise ValueError(f"matter is already client-bound: {source}")

    directory_name = f"{datetime.now().strftime('%Y%m%d')}-{matter_type}-{matter_slug}"
    destination = client_path / "matters" / "open" / directory_name
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    original_relative = str(source.relative_to(paths.project_root))
    shutil.move(str(source), str(destination))

    status_file = destination / "info" / "status.md"
    if status_file.is_file():
        document = read_markdown(status_file)
        metadata = dict(document.frontmatter)
        body = document.body
    else:
        ensure_chronology_file(destination)
        (destination / "info" / "obligations").mkdir(parents=True, exist_ok=True)
        (destination / "info" / "todos").mkdir(parents=True, exist_ok=True)
        (destination / "raw").mkdir(parents=True, exist_ok=True)
        (destination / "reference").mkdir(parents=True, exist_ok=True)
        metadata = {}
        body = render_template("status", paths)
    metadata.update(
        MatterStatusFrontmatter(
            matter_type=matter_type,
            priority=cast(Priority, priority),
            opened=today(),
            client=client_slug,
            workspace="client",
            bound_from=original_relative,
            billing=billing,
        ).to_dict()
    )
    write_markdown(status_file, MarkdownDocument(frontmatter=metadata, body=body))
    ensure_chronology_file(destination)
    touch_matter(destination)
    return destination
