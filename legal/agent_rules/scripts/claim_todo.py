"""Usage: claim_todo.py <slug>

Sets status: claimed and moves agent_rules/todos/<slug>.md to claimed/.
"""

from __future__ import annotations

import shutil
import sys

from _lib import die, frontmatter_set, praxis_root, validate_slug


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        die("usage: claim_todo.py <slug>")

    slug = argv[0]
    validate_slug(slug)

    root = praxis_root()
    claimed_dir = root / "agent_rules" / "todos" / "claimed"
    claimed_dir.mkdir(parents=True, exist_ok=True)
    src = root / "agent_rules" / "todos" / f"{slug}.md"
    dest = claimed_dir / f"{slug}.md"

    if not src.is_file():
        die(f"open todo not found: {slug}")
    if dest.is_file():
        die(f"already claimed: {slug}")

    frontmatter_set(src, "status", "claimed")
    shutil.move(str(src), str(dest))

    print(dest)


if __name__ == "__main__":
    main(sys.argv[1:])
