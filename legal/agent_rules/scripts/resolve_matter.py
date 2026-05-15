"""Usage: resolve_matter.py <matter_ref>

Closes a matter: sets status to 'resolved' in info/status.md frontmatter and moves
the directory from matters/open/ to matters/resolved/.
"""

from __future__ import annotations

import shutil
import sys

from _lib import (
    append_record,
    die,
    frontmatter_get,
    frontmatter_set,
    resolve_matter,
    today,
)


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        die("usage: resolve_matter.py <matter_ref>")

    matter_dir = resolve_matter(argv[0])
    status_file = matter_dir / "info" / "status.md"

    if not status_file.is_file():
        die(f"no info/status.md in {matter_dir}")

    if frontmatter_get(status_file, "status") == "resolved":
        die("matter already resolved")

    parent = matter_dir.parent
    grandparent = parent.parent
    if parent.name != "open":
        die(f"matter is not under matters/open/: {matter_dir}")

    dest = grandparent / "resolved" / matter_dir.name
    if dest.exists():
        die(f"destination already exists: {dest}")

    frontmatter_set(status_file, "status", "resolved")
    append_record(matter_dir, today(), "matter:resolved", "Matter closed.")

    shutil.move(str(matter_dir), str(dest))

    print(dest)


if __name__ == "__main__":
    main(sys.argv[1:])
