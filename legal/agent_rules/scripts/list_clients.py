"""Usage: list_clients.py

Outputs a TSV table of all clients (open and dormant).
Columns: slug | display_name | client_type | open_matters | resolved_matters
"""

from __future__ import annotations

import sys

from _lib import frontmatter_get, praxis_root


def main(argv: list[str]) -> None:
    root = praxis_root()
    clients_dir = root / "clients"

    if not clients_dir.is_dir():
        print("(no clients yet)")
        return

    profiles = sorted(clients_dir.glob("*/profile.md"))

    print("slug\tdisplay_name\tclient_type\topen_matters\tresolved_matters")

    if not profiles:
        print("(no clients yet)")
        return

    for profile in profiles:
        slug = profile.parent.name
        display = frontmatter_get(profile, "display_name")
        client_type = frontmatter_get(profile, "client_type")
        open_dir = clients_dir / slug / "matters" / "open"
        resolved_dir = clients_dir / slug / "matters" / "resolved"
        open_count = sum(1 for p in open_dir.iterdir() if p.is_dir()) if open_dir.is_dir() else 0
        resolved_count = (
            sum(1 for p in resolved_dir.iterdir() if p.is_dir()) if resolved_dir.is_dir() else 0
        )
        print(f"{slug}\t{display}\t{client_type}\t{open_count}\t{resolved_count}")


if __name__ == "__main__":
    main(sys.argv[1:])
