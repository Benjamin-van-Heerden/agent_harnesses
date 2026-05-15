"""Usage: new_client.py <slug> <display_name> <client_type>

client_type is free-form text (e.g. individual, company, close_corporation,
trust, estate, voluntary_association, ...). Used as descriptive metadata.
Creates clients/<slug>/{profile.md, matters/open/, matters/resolved/}.
"""

from __future__ import annotations

import sys

from _lib import die, praxis_root, render_skeleton, today, validate_slug


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        die("usage: new_client.py <slug> <display_name> <client_type>")

    slug, display_name, client_type = argv
    validate_slug(slug)

    root = praxis_root()
    client_dir = root / "clients" / slug
    if client_dir.is_dir():
        die(f"client already exists: {slug}")

    (client_dir / "matters" / "open").mkdir(parents=True, exist_ok=True)
    (client_dir / "matters" / "resolved").mkdir(parents=True, exist_ok=True)

    profile = client_dir / "profile.md"
    profile.write_text(
        render_skeleton(
            "profile",
            CLIENT_SLUG=slug,
            DISPLAY_NAME=display_name,
            CLIENT_TYPE=client_type,
            TODAY=today(),
        )
    )

    print(profile)


if __name__ == "__main__":
    main(sys.argv[1:])
