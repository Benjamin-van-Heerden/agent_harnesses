import tomllib
from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, matter_obligations_dir
from src.state.matters import resolve_matter
from src.state.models import ObligationRecord
from src.state.validation import validate_date, validate_slug
from src.utils.markdown import frontmatter_set


VALID_OBLIGATION_KINDS = (
    "deadline",
    "court_appearance",
    "prescription",
    "follow_up",
    "filing",
    "service",
    "preparation",
    "client_meeting",
    "other",
)
VALID_OBLIGATION_STATUSES = ("open", "done", "missed", "waived", "extended", "superseded")


def validate_obligation_kind(value: str) -> None:
    if value in VALID_OBLIGATION_KINDS:
        return
    raise ValueError(f"invalid obligation kind '{value}'")


def validate_obligation_status(value: str) -> None:
    if value in VALID_OBLIGATION_STATUSES:
        return
    raise ValueError(f"invalid obligation status '{value}'")


def obligation_content(
    obligation_id: str,
    kind: str,
    status: str,
    due_date: str,
    description: str,
    source_event: str = "",
) -> str:
    validate_slug(obligation_id)
    validate_obligation_kind(kind)
    validate_obligation_status(status)
    validate_date(due_date)
    return "\n".join(
        [
            f'id = "{obligation_id}"',
            f'kind = "{kind}"',
            f'status = "{status}"',
            f'due_date = "{due_date}"',
            f'description = "{description}"',
            f'source_event = "{source_event}"',
            "",
        ]
    )


def create_obligation(
    matter_ref: str,
    obligation_id: str,
    kind: str,
    due_date: str,
    description: str,
    status: str = "open",
    source_event: str = "",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    matter_dir = resolve_matter(matter_ref, paths)
    target = matter_obligations_dir(matter_dir) / kind / f"{due_date}-{obligation_id}.toml"
    if target.exists():
        raise FileExistsError(f"obligation already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(obligation_content(obligation_id, kind, status, due_date, description, source_event))
    if status == "open":
        open_dates = [
            parse_obligation(path).due_date
            for path in sorted(matter_obligations_dir(matter_dir).glob("*/*.toml"))
            if parse_obligation(path).status == "open"
        ]
        frontmatter_set(matter_dir / "info" / "status.md", "next_obligation", min(open_dates) if open_dates else "null")
    return target


def parse_obligation(path: Path) -> ObligationRecord:
    data = tomllib.loads(path.read_text())
    return ObligationRecord(
        obligation_id=str(data.get("id", path.stem)),
        kind=str(data.get("kind", data.get("category", ""))),
        status=str(data.get("status", "")),
        due_date=str(data.get("due_date", "")),
        description=str(data.get("description", "")),
        source_event=str(data.get("source_event", "")),
        path=path,
    )


def list_obligations(matter_ref: str, paths: ProjectPaths = PROJECT_PATHS) -> list[ObligationRecord]:
    matter_dir = resolve_matter(matter_ref, paths)
    obligations_dir = matter_obligations_dir(matter_dir)
    if not obligations_dir.is_dir():
        return []
    return [parse_obligation(path) for path in sorted(obligations_dir.glob("*/*.toml"))]


def upcoming_obligations(days: int = 14, paths: ProjectPaths = PROJECT_PATHS) -> list[tuple[str, Path, ObligationRecord]]:
    from datetime import datetime, timedelta

    from src.state.time import today

    today_date = today()
    cutoff = (datetime.strptime(today_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
    rows: list[tuple[str, Path, ObligationRecord]] = []
    for obligation_file in sorted(paths.clients_root.glob("*/matters/open/*/info/obligations/*/*.toml")):
        matter_dir = obligation_file.parent.parent.parent.parent
        obligation = parse_obligation(obligation_file)
        if obligation.status == "open" and today_date <= obligation.due_date <= cutoff:
            rows.append((obligation.due_date, matter_dir, obligation))
    return sorted(rows, key=lambda row: (row[0], str(row[1]), row[2].kind))
