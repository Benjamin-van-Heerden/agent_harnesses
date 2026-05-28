import tomllib
from pathlib import Path
from typing import Any

from src.config.models import (
    HarnessConfig,
    ImportantFileConfig,
    LegalConfig,
    LegalHarnessConfig,
    ProjectConfig,
    TreeDirConfig,
)


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def _string(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _bool(value: object, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _int(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) else default


def _config_items(raw: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = raw.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _important_files(raw: dict[str, Any]) -> list[ImportantFileConfig]:
    return [
        ImportantFileConfig(
            path=_string(item.get("path")),
            description=_string(item.get("description")),
        )
        for item in _config_items(raw, "files")
        if _string(item.get("path"))
    ]


def _tree_dirs(raw: dict[str, Any]) -> list[TreeDirConfig]:
    items = [
        TreeDirConfig(
            path=_string(item.get("path")),
            description=_string(item.get("description")),
        )
        for item in _config_items(raw, "tree_dirs")
        if _string(item.get("path"))
    ]
    if items:
        return items
    return [TreeDirConfig(path="src", description="Reusable Typst source")]


def load_config(path: Path) -> LegalHarnessConfig:
    try:
        with open(path, "rb") as file:
            raw = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        raw = {}

    project = _section(raw, "project")
    harness = _section(raw, "harness")
    legal = _section(raw, "legal")

    return LegalHarnessConfig(
        project=ProjectConfig(
            name=_string(project.get("name"), path.parent.parent.name),
            description=_string(project.get("description")),
        ),
        files=_important_files(raw),
        tree_dirs=_tree_dirs(raw),
        harness=HarnessConfig(
            name=_string(harness.get("name"), "legal"),
            local_git_snapshots=_bool(harness.get("local_git_snapshots"), True),
            last_updated_at=_string(harness.get("last_updated_at")),
            update_interval_days=_int(harness.get("update_interval_days"), 3),
        ),
        legal=LegalConfig(jurisdiction=_string(legal.get("jurisdiction"))),
    )
