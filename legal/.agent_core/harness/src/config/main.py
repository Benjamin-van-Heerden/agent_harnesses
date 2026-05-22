import tomllib
from pathlib import Path
from typing import Any

from src.config.models import HarnessConfig, LegalConfig, LegalHarnessConfig, ProjectConfig


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    return value if isinstance(value, dict) else {}


def _string(value: object, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _bool(value: object, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _int(value: object, default: int = 0) -> int:
    return value if isinstance(value, int) else default


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
        harness=HarnessConfig(
            name=_string(harness.get("name"), "legal"),
            local_git_snapshots=_bool(harness.get("local_git_snapshots"), True),
            last_updated_at=_string(harness.get("last_updated_at")),
            update_interval_days=_int(harness.get("update_interval_days"), 3),
        ),
        legal=LegalConfig(jurisdiction=_string(legal.get("jurisdiction"))),
    )
