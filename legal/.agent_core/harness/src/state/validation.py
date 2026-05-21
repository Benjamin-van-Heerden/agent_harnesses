import re


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_PRIORITIES = ("low", "normal", "high", "urgent")
VALID_TODO_PRIORITIES = ("low", "normal", "high")
VALID_DIRECTIONS = ("in", "out")


def validate_slug(value: str) -> None:
    if SLUG_RE.match(value):
        return
    raise ValueError(
        f"invalid slug '{value}' (lowercase alphanumeric, underscore, hyphen; must start with letter or digit)"
    )


def validate_date(value: str) -> None:
    if DATE_RE.match(value):
        return
    raise ValueError("date must be YYYY-MM-DD")


def validate_priority(value: str) -> None:
    if value in VALID_PRIORITIES:
        return
    raise ValueError(f"invalid priority '{value}' (low|normal|high|urgent)")


def validate_todo_priority(value: str) -> None:
    if value in VALID_TODO_PRIORITIES:
        return
    raise ValueError(f"invalid priority '{value}' (low|normal|high)")


def validate_direction(value: str) -> None:
    if value in VALID_DIRECTIONS:
        return
    raise ValueError("direction must be 'in' or 'out'")
