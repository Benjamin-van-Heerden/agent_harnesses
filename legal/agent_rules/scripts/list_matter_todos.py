"""Usage: list_matter_todos.py <matter_ref>

Lists open todos scoped to the given matter.
Output: TSV columns — slug | priority | title
"""

from __future__ import annotations

import re
import sys

from _lib import die, frontmatter_get, praxis_root, resolve_matter

H1_RE = re.compile(r"^# (.*)$")


def _first_heading(file) -> str:
    for line in file.read_text().splitlines():
        m = H1_RE.match(line)
        if m:
            return m.group(1)
    return ""


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        die("usage: list_matter_todos.py <matter_ref>")

    root = praxis_root()
    matter_dir = resolve_matter(argv[0])
    matter_ref = str(matter_dir.relative_to(root))

    todos_dir = root / "agent_rules" / "todos"
    if not todos_dir.is_dir():
        print("(no todos yet)")
        return

    rows: list[tuple[str, str, str]] = []
    for f in sorted(todos_dir.glob("*.md")):
        if not f.is_file():
            continue
        if frontmatter_get(f, "status") != "open":
            continue
        if frontmatter_get(f, "matter") != matter_ref:
            continue
        slug = frontmatter_get(f, "slug")
        priority = frontmatter_get(f, "priority")
        title = _first_heading(f)
        rows.append((slug, priority, title))

    print("slug\tpriority\ttitle")
    for row in rows:
        print("\t".join(row))
    if not rows:
        print("(no open todos for this matter)")


if __name__ == "__main__":
    main(sys.argv[1:])
