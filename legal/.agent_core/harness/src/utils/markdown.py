from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path

import yaml


@dataclass(frozen=True)
class MarkdownDocument:
    frontmatter: Mapping[str, object]
    body: str


def read_markdown(path: Path) -> MarkdownDocument:
    content = path.read_text() if path.is_file() else ""
    if not content.startswith("---\n"):
        return MarkdownDocument(frontmatter={}, body=content)

    _prefix, separator, rest = content.partition("\n---\n")
    if not separator:
        return MarkdownDocument(frontmatter={}, body=content)

    raw_metadata = yaml.safe_load(_prefix.removeprefix("---\n")) or {}
    metadata = raw_metadata if isinstance(raw_metadata, Mapping) else {}
    if rest.startswith("\n"):
        rest = rest[1:]
    return MarkdownDocument(frontmatter=metadata, body=rest)


def write_markdown(path: Path, document: MarkdownDocument) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = dict(document.frontmatter)
    if not metadata:
        path.write_text(document.body.rstrip() + "\n")
        return
    frontmatter = yaml.safe_dump(metadata, default_flow_style=False, sort_keys=False, allow_unicode=True)
    path.write_text(f"---\n{frontmatter}---\n\n{document.body.rstrip()}\n")


def frontmatter_get(path: Path, key: str) -> str:
    value = read_markdown(path).frontmatter.get(key, "")
    return "" if value is None else str(value)


def frontmatter_set(path: Path, key: str, value: str) -> None:
    document = read_markdown(path)
    if key not in document.frontmatter:
        raise KeyError(f"frontmatter key is missing: {key}")
    updated = dict(document.frontmatter)
    updated[key] = value
    write_markdown(path, MarkdownDocument(frontmatter=updated, body=document.body))
