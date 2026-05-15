"""Usage: new_matter.py <client_slug> <matter_type> <matter_slug> [priority] [billing]

matter_type: free-form slug (e.g. litigation, transaction, advisory, arbitration,
             appeal, tax, labour, family, criminal, estate, ...).
priority:    low | normal | high | urgent       (default: normal — drives onboard sort)
billing:     free-form (e.g. hourly, fixed, contingent, pro_bono, ...) — default: hourly
Creates clients/<client>/matters/open/YYYYMMDD-<type>-<slug>/{info/status.md, raw/, reference/}.
"""

from __future__ import annotations

import sys
from datetime import datetime

from _lib import (
    append_record,
    die,
    render_skeleton,
    resolve_client,
    today,
    validate_slug,
)

VALID_PRIORITIES = ("low", "normal", "high", "urgent")


def main(argv: list[str]) -> None:
    if not 3 <= len(argv) <= 5:
        die("usage: new_matter.py <client_slug> <matter_type> <matter_slug> [priority] [billing]")

    client = argv[0]
    matter_type = argv[1]
    matter_slug = argv[2]
    priority = argv[3] if len(argv) >= 4 else "normal"
    billing = argv[4] if len(argv) >= 5 else "hourly"

    validate_slug(client)
    validate_slug(matter_slug)
    validate_slug(matter_type)

    if priority not in VALID_PRIORITIES:
        die(f"invalid priority '{priority}' (low|normal|high|urgent)")

    client_dir = resolve_client(client)
    dir_name = f"{datetime.now().strftime('%Y%m%d')}-{matter_type}-{matter_slug}"
    matter_dir = client_dir / "matters" / "open" / dir_name

    if matter_dir.is_dir():
        die(f"matter already exists: {matter_dir}")

    (matter_dir / "info").mkdir(parents=True, exist_ok=True)
    (matter_dir / "raw").mkdir(parents=True, exist_ok=True)
    (matter_dir / "reference").mkdir(parents=True, exist_ok=True)

    (matter_dir / "info" / "status.md").write_text(
        render_skeleton(
            "status",
            MATTER_TYPE=matter_type,
            PRIORITY=priority,
            TODAY=today(),
            CLIENT=client,
            BILLING=billing,
        )
    )

    append_record(
        matter_dir,
        today(),
        "matter:opened",
        f"{matter_type} — {matter_slug} (priority {priority}, {billing})",
    )

    print(matter_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
