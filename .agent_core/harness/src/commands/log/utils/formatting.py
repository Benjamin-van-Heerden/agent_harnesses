from __future__ import annotations


def format_summary(record: dict) -> str:
    return f"- {record['filename']} ({record['created_at']})"
