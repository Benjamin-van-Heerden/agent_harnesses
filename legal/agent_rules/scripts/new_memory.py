"""Usage: new_memory.py <slug> <title>

Creates agent_rules/memories/<slug>.md from skeleton.
Body is left as $CONTENT placeholder — the agent fills it in via Edit.
"""

from __future__ import annotations

import sys

from _lib import die, praxis_root, render_skeleton, today, validate_slug


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        die("usage: new_memory.py <slug> <title>")

    slug, title = argv
    validate_slug(slug)

    root = praxis_root()
    memories_dir = root / "agent_rules" / "memories"
    memories_dir.mkdir(parents=True, exist_ok=True)
    file = memories_dir / f"{slug}.md"
    if file.is_file():
        die(f"memory already exists: {slug}")

    file.write_text(
        render_skeleton(
            "memory",
            SLUG=slug,
            TODAY=today(),
            TITLE=title,
            CONTENT="_TODO_",
        )
    )

    print(file)


if __name__ == "__main__":
    main(sys.argv[1:])
