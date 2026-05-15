"""Usage: record.py <matter_ref> <date> <text>

Appends a free-text 'note' entry to the matter's info/record.md.
The first line of <text> becomes the summary; remaining lines (if any) become the body.
"""

from __future__ import annotations

import re
import sys

from _lib import append_record, die, resolve_matter

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        die("usage: record.py <matter_ref> <date> <text>")

    matter_dir = resolve_matter(argv[0])
    date = argv[1]
    text = argv[2]

    if not DATE_RE.match(date):
        die("date must be YYYY-MM-DD")
    if not text:
        die("text must not be empty")

    if "\n" in text:
        summary, body = text.split("\n", 1)
    else:
        summary, body = text, ""

    append_record(matter_dir, date, "note", summary, body)

    print(matter_dir / "info" / "record.md")


if __name__ == "__main__":
    main(sys.argv[1:])
