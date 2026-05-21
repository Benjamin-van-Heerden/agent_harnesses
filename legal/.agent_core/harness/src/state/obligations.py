from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, matter_obligations_dir
from src.state.matters import resolve_matter
from src.state.models import DeadlineEntry
from src.state.validation import validate_date, validate_slug


VALID_OBLIGATION_CATEGORIES = (
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


def validate_obligation_category(value: str) -> None:
    if value in VALID_OBLIGATION_CATEGORIES:
        return
    raise ValueError(f"invalid obligation category '{value}'")


def validate_obligation_status(value: str) -> None:
    if value in VALID_OBLIGATION_STATUSES:
        return
    raise ValueError(f"invalid obligation status '{value}'")


def obligation_content(
    obligation_id: str,
    category: str,
    status: str,
    due_date: str,
    description: str,
    source_event: str = "",
) -> str:
    validate_slug(obligation_id)
    validate_obligation_category(category)
    validate_obligation_status(status)
    validate_date(due_date)
    return "\n".join(
        [
            f'id = "{obligation_id}"',
            f'category = "{category}"',
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
    category: str,
    due_date: str,
    description: str,
    status: str = "open",
    source_event: str = "",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    matter_dir = resolve_matter(matter_ref, paths)
    target = matter_obligations_dir(matter_dir) / f"{due_date}-{category}-{obligation_id}.toml"
    if target.exists():
        raise FileExistsError(f"obligation already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(obligation_content(obligation_id, category, status, due_date, description, source_event))
    return target


def deadline_to_obligation(deadline: DeadlineEntry) -> tuple[str, str, str, str]:
    category = "deadline" if deadline.category else "other"
    description = f"{deadline.category} — {deadline.description}" if deadline.category else deadline.description
    return category, deadline.status, deadline.due_date, description
