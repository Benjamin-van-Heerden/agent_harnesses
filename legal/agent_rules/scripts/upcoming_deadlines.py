"""Usage: upcoming_deadlines.py [days]

Default window: 14 days. Lists all open deadlines within the window across all
open matters, sorted by date.
Output: date | matter_path | type | description
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta

from _lib import die, praxis_root, today

LINE_RE = re.compile(r"^- \[open\] (\d{4}-\d{2}-\d{2}) — ([^—]+) — (.+)$")


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        die("usage: upcoming_deadlines.py [days]")

    try:
        days = int(argv[0]) if argv else 14
    except ValueError:
        die(f"days must be an integer, got '{argv[0]}'")

    root = praxis_root()
    today_str = today()
    cutoff = (datetime.strptime(today_str, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")

    deadline_files = sorted((root / "clients").glob("*/matters/open/*/info/deadlines.md"))

    rows: list[tuple[str, str, str, str]] = []
    for dfile in deadline_files:
        matter_dir = dfile.parent.parent
        rel = str(matter_dir.relative_to(root))
        for line in dfile.read_text().splitlines():
            m = LINE_RE.match(line)
            if not m:
                continue
            d, t, desc = m.group(1), m.group(2).strip(), m.group(3)
            if d < today_str or d > cutoff:
                continue
            rows.append((d, rel, t, desc))

    print("date\tmatter\ttype\tdescription")
    for row in rows:
        print("\t".join(row))
    if not rows:
        print(f"(no deadlines within {days} days)")


if __name__ == "__main__":
    main(sys.argv[1:])
