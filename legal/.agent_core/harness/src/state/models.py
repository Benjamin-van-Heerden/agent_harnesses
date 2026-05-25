from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClientProfile:
    client_slug: str
    display_name: str
    client_type: str
    opened: str
    status: str
    path: Path


@dataclass(frozen=True)
class MatterStatus:
    matter_type: str
    status: str
    priority: str
    opened: str
    client: str
    billing: str
    case_number: str | None
    physical_files: list[str]
    workflow: str | None
    last_touched_at: str | None
    next_obligation: str
    tags: list[str]
    path: Path
    matter_dir: Path


@dataclass(frozen=True)
class MatterRef:
    client_slug: str
    matter_slug: str
    matter_dir: Path
    status_file: Path
    is_resolved: bool


@dataclass(frozen=True)
class ObligationRecord:
    obligation_id: str
    kind: str
    status: str
    due_date: str
    description: str
    source_event: str
    path: Path


@dataclass(frozen=True)
class ChronologyEntry:
    date: str
    kind: str
    summary: str
    body: str = ""


@dataclass(frozen=True)
class TodoRecord:
    slug: str
    created: str
    status: str
    priority: str
    matter: str
    title: str
    path: Path


@dataclass(frozen=True)
class MemoryRecord:
    slug: str
    created: str
    title: str
    path: Path


@dataclass(frozen=True)
class WorkLogRecord:
    date: str
    session_start: str
    matter: str
    path: Path
