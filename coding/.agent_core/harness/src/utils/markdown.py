from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---"):
        return {}, content

    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if match is None:
        return {}, content

    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, content

    if not isinstance(metadata, dict):
        return {}, content

    return metadata, match.group(2)


def dump_frontmatter(metadata: dict[str, Any], body: str) -> str:
    if not metadata:
        return body

    frontmatter = yaml.dump(
        metadata,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    if body and not body.startswith("\n"):
        body = "\n" + body
    return f"---\n{frontmatter}---{body}"


def read_markdown(path: Path) -> tuple[dict[str, Any], str]:
    return parse_frontmatter(path.read_text())


def write_markdown(path: Path, metadata: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_frontmatter(metadata, body))


def slugify(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r"[\s\-]+", "_", slug)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")
