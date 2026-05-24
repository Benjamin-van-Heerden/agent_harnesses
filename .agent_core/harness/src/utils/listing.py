from datetime import datetime


def short_datetime(value: str | None) -> str:
    if not value:
        return "N/A"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def short_date(value: str | None) -> str:
    if not value:
        return "N/A"
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d")
    except ValueError:
        return value


def truncate(value: str | None, width: int) -> str:
    text = value or "N/A"
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return f"{text[: width - 3]}..."


def table_lines(columns: list[tuple[str, int]], rows: list[list[str]]) -> list[str]:
    header = "  ".join(label.ljust(width) for label, width in columns)
    divider = "  ".join("-" * width for _, width in columns)
    lines = [header, divider]
    for row in rows:
        cells = [
            truncate(value, width).ljust(width)
            for value, (_, width) in zip(row, columns, strict=True)
        ]
        lines.append("  ".join(cells))
    return lines
