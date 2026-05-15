"""Usage: list_open_matters.py

Outputs a TSV table of all open matters across all clients.
Columns: client | matter | type | priority | next_deadline | open_todos | path
"""

from __future__ import annotations

import sys
from collections import Counter

from _lib import frontmatter_get, praxis_root


def main(argv: list[str]) -> None:
    root = praxis_root()
    clients_dir = root / "clients"
    todos_dir = root / "agent_rules" / "todos"

    if not clients_dir.is_dir():
        print("(no clients yet)")
        return

    todo_counts: Counter[str] = Counter()
    if todos_dir.is_dir():
        for f in todos_dir.glob("*.md"):
            if not f.is_file():
                continue
            if frontmatter_get(f, "status") != "open":
                continue
            matter = frontmatter_get(f, "matter")
            if not matter or matter == "null":
                continue
            todo_counts[matter] += 1

    status_files = sorted(clients_dir.glob("*/matters/open/*/info/status.md"))

    print("client\tmatter\ttype\tpriority\tnext_deadline\topen_todos\tpath")

    if not status_files:
        print("(no open matters)")
        return

    for status_file in status_files:
        matter_dir = status_file.parent.parent  # .../matters/open/<matter>
        matter_name = matter_dir.name
        client = matter_dir.parent.parent.parent.name  # .../<client>/matters/open/<matter>
        type_ = frontmatter_get(status_file, "matter_type")
        priority = frontmatter_get(status_file, "priority")
        deadline = frontmatter_get(status_file, "next_deadline")
        rel = str(matter_dir.relative_to(root))
        todos = todo_counts.get(rel, 0)
        print(f"{client}\t{matter_name}\t{type_}\t{priority}\t{deadline}\t{todos}\t{rel}")


if __name__ == "__main__":
    main(sys.argv[1:])
