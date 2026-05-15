from __future__ import annotations

from src.state.models import WorkLog


def format_summary(record: WorkLog) -> str:
    return f"- {record.filename} ({record.created_at})"
