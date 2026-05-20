from src.state.models import Task


def format_summary(record: Task) -> str:
    return f"- [{record.status}] {record.slug}: {record.title}"


def format_detail(record: Task) -> str:
    lines = [
        f"# {record.title}",
        f"Slug: {record.slug}",
        f"Status: {record.status}",
        f"File: {record.filename}",
        "",
        record.body.strip(),
    ]
    return "\n".join(lines).rstrip()
