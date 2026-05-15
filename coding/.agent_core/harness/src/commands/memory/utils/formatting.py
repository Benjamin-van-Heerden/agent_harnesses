from src.state.models import Memory


def format_summary(record: Memory) -> str:
    return f"- {record.title} ({record.slug})"


def format_detail(record: Memory) -> str:
    lines = [
        f"# {record.title}",
        "",
        record.body.strip(),
    ]
    return "\n".join(lines).rstrip()
