"""Usage: new_log.py [matter_ref]

Creates agent_rules/log/<YYYYMMDD-HHMMSS>_log.md from skeleton.
"""

from __future__ import annotations

import sys

from _lib import die, now_stamp, now_time, praxis_root, render_skeleton, resolve_matter, today


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        die("usage: new_log.py [matter_ref]")

    root = praxis_root()
    matter_ref = "null"
    if argv and argv[0]:
        matter_dir = resolve_matter(argv[0])
        matter_ref = str(matter_dir.relative_to(root))

    log_dir = root / "agent_rules" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    file = log_dir / f"{now_stamp()}_log.md"

    file.write_text(
        render_skeleton(
            "log",
            TODAY=today(),
            TIME=now_time(),
            MATTER_REF=matter_ref,
        )
    )

    print(file)


if __name__ == "__main__":
    main(sys.argv[1:])
