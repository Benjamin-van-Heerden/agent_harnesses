"""Shared helpers for praxis scripts.

Conventions:
  - All scripts run from anywhere inside a praxis project (auto-resolved via praxis_root).
  - All paths returned/printed are relative to project root unless noted.
  - Errors go to stderr with prefix "praxis:". Successful output goes to stdout.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import NoReturn


def die(msg: str) -> NoReturn:
    print(f"praxis: {msg}", file=sys.stderr)
    sys.exit(1)


def praxis_root() -> Path:
    d = Path.cwd().resolve()
    for candidate in [d, *d.parents]:
        if (candidate / "agent_rules" / "skeletons").is_dir():
            return candidate
    die("not inside a praxis project (no agent_rules/skeletons/ found in any parent)")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def validate_slug(s: str) -> None:
    if not _SLUG_RE.match(s):
        die(
            f"invalid slug '{s}' (lowercase alphanumeric, underscore, hyphen; "
            "must start with letter or digit)"
        )


def _frontmatter_lines(file: Path) -> tuple[list[str], int, int] | None:
    """Return (all_lines, fm_start_idx, fm_end_idx) where fm_start/end point to
    the lines containing the leading and trailing '---'. Returns None if no
    frontmatter block."""
    try:
        text = file.read_text()
    except FileNotFoundError:
        return None
    lines = text.splitlines(keepends=True)
    fm_start = None
    fm_end = None
    for i, line in enumerate(lines):
        if re.match(r"^---[ \t]*$", line.rstrip("\n")):
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break
    if fm_start is None or fm_end is None:
        return None
    return lines, fm_start, fm_end


def frontmatter_get(file: Path | str, key: str) -> str:
    """Read a top-level scalar value from YAML frontmatter. Returns '' if absent."""
    file = Path(file)
    parsed = _frontmatter_lines(file)
    if parsed is None:
        return ""
    lines, fm_start, fm_end = parsed
    pat = re.compile(rf"^{re.escape(key)}:[ \t]*(.*)$")
    for line in lines[fm_start + 1 : fm_end]:
        stripped = line.rstrip("\n")
        m = pat.match(stripped)
        if m:
            return m.group(1)
    return ""


def frontmatter_set(file: Path | str, key: str, value: str) -> None:
    """Replace a top-level scalar value in YAML frontmatter. Errors if key absent."""
    file = Path(file)
    parsed = _frontmatter_lines(file)
    if parsed is None:
        die(f"key '{key}' not present in frontmatter of {file}")
        return
    lines, fm_start, fm_end = parsed
    pat = re.compile(rf"^{re.escape(key)}:")
    for i in range(fm_start + 1, fm_end):
        if pat.match(lines[i].rstrip("\n")):
            newline = "\n" if lines[i].endswith("\n") else ""
            lines[i] = f"{key}: {value}{newline}"
            file.write_text("".join(lines))
            return
    die(f"key '{key}' not present in frontmatter of {file}")


def render_skeleton(name: str, **kwargs: str) -> str:
    """Render a skeleton, substituting $KEY tokens (literal, not regex)."""
    root = praxis_root()
    file = root / "agent_rules" / "skeletons" / f"{name}.md"
    if not file.is_file():
        die(f"skeleton not found: {file}")
    content = file.read_text()
    for key, value in kwargs.items():
        content = content.replace(f"${key}", value)
    if not content.endswith("\n"):
        content += "\n"
    return content


def resolve_client(slug: str) -> Path:
    root = praxis_root()
    d = root / "clients" / slug
    if not d.is_dir():
        die(f"client not found: {slug}")
    return d


def resolve_matter(input_ref: str) -> Path:
    """Resolve a matter ref to a full directory path.

    Accepts: full path, partial matter dir name, or unique substring of matter
    dir name. Searches both open/ and resolved/ across all clients.
    """
    root = praxis_root()

    # Case 1: existing path that has info/status.md.
    cand = root / input_ref
    if cand.is_dir() and (cand / "info" / "status.md").is_file():
        return cand
    cand2 = Path(input_ref)
    if cand2.is_dir() and (cand2 / "info" / "status.md").is_file():
        return cand2.resolve()

    # Case 2: substring search of matter dir names at depth 4 below clients/.
    # Mirrors `find $root/clients -mindepth 4 -maxdepth 4 -type d -name "*input*"`.
    clients_dir = root / "clients"
    matches: list[Path] = []
    if clients_dir.is_dir():
        for client in sorted(p for p in clients_dir.iterdir() if p.is_dir()):
            for bucket in ("open", "resolved"):
                bucket_dir = client / "matters" / bucket
                if not bucket_dir.is_dir():
                    continue
                for matter in sorted(p for p in bucket_dir.iterdir() if p.is_dir()):
                    if input_ref in matter.name:
                        matches.append(matter)

    if not matches:
        die(f"no matter found matching '{input_ref}'")
    if len(matches) > 1:
        print(f"praxis: multiple matters match '{input_ref}':", file=sys.stderr)
        for m in matches:
            print(str(m), file=sys.stderr)
        sys.exit(1)
    return matches[0]


def ensure_file_from_skeleton(file: Path | str, skeleton: str) -> None:
    """Copy a skeleton file to `file` if it doesn't already exist."""
    file = Path(file)
    if file.is_file():
        return
    root = praxis_root()
    src = root / "agent_rules" / "skeletons" / f"{skeleton}.md"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(src.read_bytes())


def append_record(
    matter_dir: Path | str,
    date: str,
    kind: str,
    summary: str,
    body: str = "",
) -> None:
    """Append an entry to a matter's info/record.md. Creates the file if absent.

    Output format:
        ## <date> — <kind> — <summary>

        <body if non-empty>
    """
    matter_dir = Path(matter_dir)
    file = matter_dir / "info" / "record.md"
    ensure_file_from_skeleton(file, "record")
    out = [f"\n## {date} — {kind} — {summary}\n"]
    if body:
        out.append(f"\n{body}\n")
    with file.open("a") as f:
        f.write("".join(out))
