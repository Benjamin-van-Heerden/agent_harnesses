from pathlib import Path

from src.state.models import ChronologyEntry
from src.state.templates import ensure_file_from_template


def append_record(matter_dir: Path, entry: ChronologyEntry) -> Path:
    file = matter_dir / "info" / "record.md"
    ensure_file_from_template(file, "record")

    output = [f"\n## {entry.date} — {entry.kind} — {entry.summary}\n"]
    if entry.body:
        output.append(f"\n{entry.body}\n")
    with file.open("a") as handle:
        handle.write("".join(output))
    return file
