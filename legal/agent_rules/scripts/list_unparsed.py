"""Usage: list_unparsed.py <matter_ref>

Lists files in the matter's raw/ that have no corresponding file in reference/
(matched by basename without extension).
"""

from __future__ import annotations

import sys

from _lib import die, resolve_matter


def main(argv: list[str]) -> None:
    if len(argv) != 1:
        die("usage: list_unparsed.py <matter_ref>")

    matter_dir = resolve_matter(argv[0])
    raw = matter_dir / "raw"
    ref = matter_dir / "reference"

    if not raw.is_dir():
        print("(no raw/ directory)")
        return

    raw_files = sorted(p for p in raw.iterdir() if p.is_file())

    ref_stems: set[str] = set()
    if ref.is_dir():
        for p in ref.iterdir():
            if p.is_file():
                ref_stems.add(p.stem)

    found = False
    for f in raw_files:
        if f.stem not in ref_stems:
            print(f)
            found = True

    if not found:
        print("(all raw files have a reference counterpart)")


if __name__ == "__main__":
    main(sys.argv[1:])
