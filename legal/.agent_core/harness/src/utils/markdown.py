from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarkdownDocument:
    frontmatter: dict[str, str]
    body: str


def read_markdown(path: Path) -> MarkdownDocument:
    content = path.read_text() if path.is_file() else ""
    if not content.startswith("---\n"):
        return MarkdownDocument(frontmatter={}, body=content)

    _prefix, separator, rest = content.partition("\n---\n")
    if not separator:
        return MarkdownDocument(frontmatter={}, body=content)

    metadata: dict[str, str] = {}
    for line in _prefix.splitlines()[1:]:
        key, colon, value = line.partition(":")
        if colon:
            metadata[key.strip()] = value.strip().strip("'\"")
    if rest.startswith("\n"):
        rest = rest[1:]
    return MarkdownDocument(frontmatter=metadata, body=rest)


def write_markdown(path: Path, document: MarkdownDocument) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key, value in document.frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(document.body.rstrip())
    path.write_text("\n".join(lines).rstrip() + "\n")


def frontmatter_get(path: Path, key: str) -> str:
    return read_markdown(path).frontmatter.get(key, "")


def frontmatter_set(path: Path, key: str, value: str) -> None:
    document = read_markdown(path)
    if key not in document.frontmatter:
        raise KeyError(f"frontmatter key is missing: {key}")
    updated = dict(document.frontmatter)
    updated[key] = value
    write_markdown(path, MarkdownDocument(frontmatter=updated, body=document.body))
