"""Usage: log_communication.py <matter_ref> <date> <direction> <medium> <counterparty> <subject>

direction: in | out                    (semantic — kept enforced)
medium:    free-form (e.g. letter, email, call, meeting, court_filing, sms, whatsapp, ...)
Appends an entry to <matter>/info/record.md. Body is left as _TODO_ —
the agent fills it in afterwards via Edit.
"""

from __future__ import annotations

import re
import sys

from _lib import append_record, die, resolve_matter

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main(argv: list[str]) -> None:
    if len(argv) != 6:
        die(
            "usage: log_communication.py <matter_ref> <date> <direction> "
            "<medium> <counterparty> <subject>"
        )

    matter_dir = resolve_matter(argv[0])
    date, direction, medium, counterparty, subject = argv[1], argv[2], argv[3], argv[4], argv[5]

    if direction not in ("in", "out"):
        die("direction must be 'in' or 'out'")
    if not DATE_RE.match(date):
        die("date must be YYYY-MM-DD")

    kind = f"comm:{direction}:{medium}"
    summary = f"{counterparty} — {subject}"
    body = "_TODO: body_"

    append_record(matter_dir, date, kind, summary, body)

    print(matter_dir / "info" / "record.md")


if __name__ == "__main__":
    main(sys.argv[1:])
