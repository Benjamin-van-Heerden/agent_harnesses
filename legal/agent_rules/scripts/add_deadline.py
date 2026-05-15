"""Usage: add_deadline.py <matter_ref> <date> <type> <description>

Appends an open deadline to <matter>/info/deadlines.md and updates next_deadline
in info/status.md to the earliest open deadline.
"""

from __future__ import annotations

import re
import sys

from _lib import (
    append_record,
    die,
    ensure_file_from_skeleton,
    frontmatter_set,
    resolve_matter,
    today,
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OPEN_LINE_RE = re.compile(r"^- \[open\] (\d{4}-\d{2}-\d{2}) ")


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        die("usage: add_deadline.py <matter_ref> <date> <type> <description>")

    matter_dir = resolve_matter(argv[0])
    date, type_, description = argv[1], argv[2], argv[3]

    if not DATE_RE.match(date):
        die("date must be YYYY-MM-DD")

    file = matter_dir / "info" / "deadlines.md"
    ensure_file_from_skeleton(file, "deadlines")

    with file.open("a") as f:
        f.write(f"- [open] {date} — {type_} — {description}\n")

    open_dates = []
    for line in file.read_text().splitlines():
        m = OPEN_LINE_RE.match(line)
        if m:
            open_dates.append(m.group(1))
    next_deadline = min(open_dates) if open_dates else "null"

    frontmatter_set(matter_dir / "info" / "status.md", "next_deadline", next_deadline)

    append_record(matter_dir, today(), "deadline:added", f"{date} — {type_} — {description}")

    print(file)


if __name__ == "__main__":
    main(sys.argv[1:])
