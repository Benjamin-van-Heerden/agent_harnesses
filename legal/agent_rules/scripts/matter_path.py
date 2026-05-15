"""Usage: matter_path.py <ref>

Resolves a matter reference (slug, partial dir name, or path) to a unique full path.
Errors if zero or multiple matches.
"""

from __future__ import annotations

import sys

from _lib import die, resolve_matter


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        die("usage: matter_path.py <ref>")
    print(resolve_matter(argv[0]))


if __name__ == "__main__":
    main(sys.argv[1:])
