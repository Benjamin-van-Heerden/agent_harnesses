import hashlib
import json
import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from src.config.paths import PROJECT_PATHS


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class OptionalDocsError(Exception):
    pass


class OptionalDocRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=SLUG_PATTERN.pattern)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class OptionalDocsManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    docs: list[OptionalDocRecord] = Field(default_factory=list)


class OptionalDocStatus(BaseModel):
    slug: str
    status: str


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def catalog() -> dict[str, Path]:
    catalog_dir = PROJECT_PATHS.optional_docs_catalog_dir
    if not catalog_dir.is_dir():
        raise OptionalDocsError(f"optional doc catalog is missing: {catalog_dir}")
    available = {path.stem: path for path in sorted(catalog_dir.glob("*.md")) if path.is_file()}
    invalid = [slug for slug in available if not SLUG_PATTERN.fullmatch(slug)]
    if invalid:
        raise OptionalDocsError(f"optional doc catalog contains invalid slug(s): {', '.join(invalid)}")
    return available


def load_manifest() -> OptionalDocsManifest:
    path = PROJECT_PATHS.optional_docs_file
    if not path.exists():
        return OptionalDocsManifest()
    try:
        with open(path, "rb") as file:
            return OptionalDocsManifest.model_validate(tomllib.load(file))
    except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
        raise OptionalDocsError(f"could not read {path}: {error}") from error


def write_manifest(records: dict[str, OptionalDocRecord]) -> None:
    path = PROJECT_PATHS.optional_docs_file
    if not records:
        if path.exists():
            path.unlink()
        return

    lines = ["# Optional docs managed by Agent Core"]
    for slug, record in sorted(records.items()):
        lines.extend(
            [
                "",
                "[[docs]]",
                f"slug = {json.dumps(slug)}",
                f"source_sha256 = {json.dumps(record.source_sha256)}",
            ]
        )
    path.write_text("\n".join(lines) + "\n")


def records_by_slug(manifest: OptionalDocsManifest) -> dict[str, OptionalDocRecord]:
    records: dict[str, OptionalDocRecord] = {}
    for record in manifest.docs:
        if record.slug in records:
            raise OptionalDocsError(f"duplicate optional doc record: {record.slug}")
        records[record.slug] = record
    return records


def validate_slugs(slugs: list[str], available: dict[str, Path]) -> list[str]:
    if not slugs:
        raise OptionalDocsError("at least one optional doc slug is required")

    invalid = sorted({slug for slug in slugs if not SLUG_PATTERN.fullmatch(slug)})
    if invalid:
        raise OptionalDocsError(f"invalid optional doc slug(s): {', '.join(invalid)}. Slugs may contain lowercase letters, numbers, and underscores")

    unknown = sorted({slug for slug in slugs if slug not in available})
    if unknown:
        choices = ", ".join(sorted(available)) or "none"
        raise OptionalDocsError(f"unknown optional doc slug(s): {', '.join(unknown)}. Available slugs: {choices}")

    return list(dict.fromkeys(slugs))


def list_statuses() -> list[OptionalDocStatus]:
    available = catalog()
    records = records_by_slug(load_manifest())
    statuses: list[OptionalDocStatus] = []
    for slug in sorted(set(available) | set(records)):
        target = PROJECT_PATHS.docs_dir / f"{slug}.md"
        record = records.get(slug)
        if record is None:
            status = "unmanaged" if target.exists() else "available"
        elif slug not in available:
            status = "unavailable"
        elif not target.exists():
            status = "missing"
        elif file_sha256(target) != record.source_sha256:
            status = "modified"
        elif file_sha256(available[slug]) != record.source_sha256:
            status = "outdated"
        else:
            status = "installed"
        statuses.append(OptionalDocStatus(slug=slug, status=status))
    return statuses


def add(slugs: list[str], force: bool = False) -> list[str]:
    available = catalog()
    selected = validate_slugs(slugs, available)
    records = records_by_slug(load_manifest())

    conflicts = [
        slug
        for slug in selected
        if slug not in records
        and (PROJECT_PATHS.docs_dir / f"{slug}.md").exists()
        and file_sha256(PROJECT_PATHS.docs_dir / f"{slug}.md") != file_sha256(available[slug])
    ]
    if conflicts and not force:
        raise OptionalDocsError(f"refusing to overwrite unmanaged doc(s): {', '.join(conflicts)}. Re-run with --force to manage and replace them")

    installed = [slug for slug in selected if slug in records]
    if installed:
        raise OptionalDocsError(f"optional doc(s) already installed: {', '.join(installed)}")

    PROJECT_PATHS.docs_dir.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []
    for slug in selected:
        source = available[slug]
        target = PROJECT_PATHS.docs_dir / source.name
        target.write_bytes(source.read_bytes())
        records[slug] = OptionalDocRecord(slug=slug, source_sha256=file_sha256(source))
        messages.append(f"Added optional doc: {slug}")
    write_manifest(records)
    return messages


def selected_records(slugs: list[str], available: dict[str, Path], records: dict[str, OptionalDocRecord], require_available: bool) -> list[str]:
    validation_catalog = available if require_available else {slug: Path() for slug in set(available) | set(records)}
    selected = validate_slugs(slugs, validation_catalog) if slugs else sorted(records)
    uninstalled = [slug for slug in selected if slug not in records]
    if uninstalled:
        raise OptionalDocsError(f"optional doc(s) are not installed: {', '.join(uninstalled)}")
    unavailable = [slug for slug in selected if slug not in available]
    if require_available and unavailable:
        raise OptionalDocsError(f"optional doc(s) are no longer available in the catalog: {', '.join(unavailable)}")
    return selected


def modified_slugs(slugs: list[str], records: dict[str, OptionalDocRecord]) -> list[str]:
    modified: list[str] = []
    for slug in slugs:
        target = PROJECT_PATHS.docs_dir / f"{slug}.md"
        if target.exists() and file_sha256(target) != records[slug].source_sha256:
            modified.append(slug)
    return modified


def update(slugs: list[str], force: bool = False) -> list[str]:
    available = catalog()
    records = records_by_slug(load_manifest())
    selected = selected_records(slugs, available, records, require_available=True)
    if not selected:
        return ["No optional docs are installed."]

    modified = modified_slugs(selected, records)
    if modified and not force:
        raise OptionalDocsError(f"refusing to overwrite locally modified doc(s): {', '.join(modified)}. Re-run with --force to replace them")

    messages: list[str] = []
    for slug in selected:
        source = available[slug]
        target = PROJECT_PATHS.docs_dir / source.name
        target.write_bytes(source.read_bytes())
        records[slug] = OptionalDocRecord(slug=slug, source_sha256=file_sha256(source))
        messages.append(f"Updated optional doc: {slug}")
    write_manifest(records)
    return messages


def remove(slugs: list[str], force: bool = False) -> list[str]:
    available = catalog()
    records = records_by_slug(load_manifest())
    selected = selected_records(slugs, available, records, require_available=False)
    modified = modified_slugs(selected, records)
    if modified and not force:
        raise OptionalDocsError(f"refusing to remove locally modified doc(s): {', '.join(modified)}. Re-run with --force to remove them")

    messages: list[str] = []
    for slug in selected:
        target = PROJECT_PATHS.docs_dir / f"{slug}.md"
        if target.exists():
            target.unlink()
        del records[slug]
        messages.append(f"Removed optional doc: {slug}")
    write_manifest(records)
    return messages
