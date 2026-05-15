"""Usage: find_matter.py <pattern>

Substring search across open and resolved matter directory names.
Outputs matching paths (relative to praxis root), one per line, sorted.
"""

from __future__ import annotations

import sys

from _lib import die, praxis_root


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        die("usage: find_matter.py <pattern>")

    pattern = argv[0]
    root = praxis_root()
    clients_dir = root / "clients"
    if not clients_dir.is_dir():
        return

    matches: list[str] = []
    for client in sorted(p for p in clients_dir.iterdir() if p.is_dir()):
        for bucket in ("open", "resolved"):
            bucket_dir = client / "matters" / bucket
            if not bucket_dir.is_dir():
                continue
            for matter in bucket_dir.iterdir():
                if matter.is_dir() and pattern in matter.name:
                    matches.append(str(matter.relative_to(root)))

    for line in sorted(matches):
        print(line)


if __name__ == "__main__":
    main(sys.argv[1:])
