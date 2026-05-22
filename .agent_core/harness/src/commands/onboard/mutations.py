import os
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal


EntryKind = Literal["directory", "file", "symlink", "other"]


@dataclass(frozen=True)
class SnapshotEntry:
    kind: EntryKind
    signature: str


@dataclass(frozen=True)
class MutationSummary:
    created: list[str]
    modified: list[str]
    deleted: list[str]

    @property
    def changed(self) -> bool:
        return bool(self.created or self.modified or self.deleted)

    @property
    def only_tmp_changed(self) -> bool:
        changed_paths = [*self.created, *self.modified, *self.deleted]
        return bool(changed_paths) and all(path.startswith(".agent_core/tmp/") for path in changed_paths)


def _display_path(root: Path, path: Path) -> str:
    return f"{root.name}/{path.relative_to(root).as_posix()}"


def _file_signature(path: Path) -> str:
    try:
        digest = sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        return f"unreadable:{error.__class__.__name__}"
    return f"sha256:{digest}"


def _entry_for(path: Path) -> SnapshotEntry:
    if path.is_symlink():
        try:
            target = os.readlink(path)
        except OSError as error:
            target = f"unreadable:{error.__class__.__name__}"
        return SnapshotEntry(kind="symlink", signature=target)

    try:
        stat = path.stat()
    except OSError as error:
        return SnapshotEntry(kind="other", signature=f"unreadable:{error.__class__.__name__}")

    if path.is_dir():
        return SnapshotEntry(kind="directory", signature="directory")
    if path.is_file():
        return SnapshotEntry(kind="file", signature=_file_signature(path))
    return SnapshotEntry(kind="other", signature=f"mode:{stat.st_mode}:mtime:{stat.st_mtime_ns}:size:{stat.st_size}")


def snapshot_agent_core(root: Path) -> dict[str, SnapshotEntry]:
    if not root.exists():
        return {}

    entries: dict[str, SnapshotEntry] = {}
    for path in sorted(root.rglob("*")):
        entries[_display_path(root, path)] = _entry_for(path)
    return entries


def summarize_mutations(
    before: dict[str, SnapshotEntry],
    after: dict[str, SnapshotEntry],
) -> MutationSummary:
    before_paths = set(before)
    after_paths = set(after)
    created = sorted(after_paths - before_paths)
    deleted = sorted(before_paths - after_paths)
    modified = sorted(path for path in before_paths & after_paths if before[path] != after[path])
    return MutationSummary(created=created, modified=modified, deleted=deleted)


def render_mutation_summary(summary: MutationSummary) -> list[str]:
    if summary.only_tmp_changed:
        return []

    lines = [
        "---",
        ".agent_core changes",
        "---",
    ]
    if not summary.changed:
        return [
            *lines,
            "No .agent_core changes detected.",
            "---",
        ]

    lines.append(
        f"Created: {len(summary.created)} | Modified: {len(summary.modified)} | Deleted: {len(summary.deleted)}"
    )
    for label, paths in (
        ("Created", summary.created),
        ("Modified", summary.modified),
        ("Deleted", summary.deleted),
    ):
        if not paths:
            continue
        lines.append(f"{label}:")
        for path in paths:
            lines.append(f"  - {path}")
    lines.append("---")
    return lines
