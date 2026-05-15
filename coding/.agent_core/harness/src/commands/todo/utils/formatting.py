from __future__ import annotations

from src.state.models import Todo


def format_summary(record: Todo) -> str:
    return f"- [{record.status}] {record.title}"


def format_detail(record: Todo) -> str:
    lines = [
        f"# {record.title}",
        f"Status: {record.status}",
        "",
        record.body.strip(),
    ]
    return "\n".join(lines).rstrip()
