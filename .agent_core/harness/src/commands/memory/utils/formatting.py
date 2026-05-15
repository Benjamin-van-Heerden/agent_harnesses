from __future__ import annotations


def format_summary(record: dict) -> str:
    title = record.get("title", record["slug"])
    return f"- {title} ({record['slug']})"


def format_detail(record: dict) -> str:
    lines = [
        f"# {record.get('title', record['slug'])}",
        "",
        record.get("body", "").strip(),
    ]
    return "\n".join(lines).rstrip()
