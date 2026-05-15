from __future__ import annotations


def format_summary(record: dict) -> str:
    status = record.get("status", "open")
    title = record.get("title", record["slug"])
    return f"- [{status}] {title}"


def format_detail(record: dict) -> str:
    lines = [
        f"# {record.get('title', record['slug'])}",
        f"Status: {record.get('status', 'open')}",
        "",
        record.get("body", "").strip(),
    ]
    return "\n".join(lines).rstrip()
