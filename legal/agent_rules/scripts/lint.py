"""Usage: lint.py

Validates frontmatter on all clients and matters. Exits non-zero if any issue.
"""

from __future__ import annotations

import sys
from pathlib import Path

from _lib import frontmatter_get, praxis_root


def main(argv: list[str]) -> None:
    root = praxis_root()
    errors: list[str] = []

    def check_required(file: Path, key: str) -> None:
        if not frontmatter_get(file, key):
            errors.append(f"  ✗ {file}: missing required key '{key}'")

    def check_in_set(file: Path, key: str, allowed: tuple[str, ...]) -> None:
        v = frontmatter_get(file, key)
        if not v:
            return
        if v not in allowed:
            errors.append(f"  ✗ {file}: '{key}' = '{v}' (allowed: {'|'.join(allowed)})")

    # Profiles: required keys + status (drives the active/resolved distinction).
    for f in (root / "clients").glob("*/profile.md"):
        check_required(f, "client_slug")
        check_required(f, "display_name")
        check_required(f, "client_type")
        check_in_set(f, "status", ("active", "resolved"))

    # Statuses: required keys + the two enums that drive logic (status, priority).
    for f in (root / "clients").glob("*/matters/*/*/info/status.md"):
        check_required(f, "matter_type")
        check_required(f, "client")
        check_required(f, "billing")
        check_in_set(f, "status", ("active", "on_hold", "resolved"))
        check_in_set(f, "priority", ("low", "normal", "high", "urgent"))

    if not errors:
        print("✓ all frontmatter valid")
        return

    for e in errors:
        print(e)
    print()
    print(f"{len(errors)} issue(s) found")
    sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
