from src.state.models import Spec


def format_summary(record: Spec) -> str:
    return f"- [{record.status}] {record.title}"


def format_detail(record: Spec) -> str:
    lines = [
        f"# {record.title}",
        f"Status: {record.status}",
        "",
        record.body.strip(),
    ]
    return "\n".join(lines).rstrip()
