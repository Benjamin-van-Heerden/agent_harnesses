"""Usage: new_todo.py <slug> <title> [priority] [matter_ref]

priority: low | normal | high  (default: normal)
Creates agent_rules/todos/<slug>.md from skeleton.
"""

from __future__ import annotations

import sys

from _lib import die, praxis_root, render_skeleton, resolve_matter, today, validate_slug

VALID_PRIORITIES = ("low", "normal", "high")


def main(argv: list[str]) -> None:
    if not 2 <= len(argv) <= 4:
        die("usage: new_todo.py <slug> <title> [priority] [matter_ref]")

    slug = argv[0]
    title = argv[1]
    priority = argv[2] if len(argv) >= 3 else "normal"
    matter_input = argv[3] if len(argv) >= 4 else ""

    validate_slug(slug)
    if priority not in VALID_PRIORITIES:
        die(f"invalid priority '{priority}'")

    root = praxis_root()
    matter_ref = "null"
    if matter_input:
        matter_dir = resolve_matter(matter_input)
        matter_ref = str(matter_dir.relative_to(root))

    todos_dir = root / "agent_rules" / "todos"
    todos_dir.mkdir(parents=True, exist_ok=True)
    file = todos_dir / f"{slug}.md"
    if file.is_file():
        die(f"todo already exists: {slug}")

    file.write_text(
        render_skeleton(
            "todo",
            SLUG=slug,
            TODAY=today(),
            PRIORITY=priority,
            MATTER_REF=matter_ref,
            TITLE=title,
            DESCRIPTION="_TODO_",
        )
    )

    print(file)


if __name__ == "__main__":
    main(sys.argv[1:])
