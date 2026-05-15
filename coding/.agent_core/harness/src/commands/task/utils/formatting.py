from __future__ import annotations

from src.state.models import Task


def format_summary(record: Task) -> str:
    return f"- [{record.status}] {record.title}"


def format_detail(record: Task) -> str:
    lines = [
        f"# {record.title}",
        f"Status: {record.status}",
        "",
        record.body.strip(),
    ]
    return "\n".join(lines).rstrip()
