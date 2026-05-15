from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic import BaseModel, ValidationError

from src.config.models import AgentCoreConfig, BranchConfig, ProjectConfig, WorktreeConfig


@dataclass(frozen=True)
class ConfigLoadResult:
    raw: dict[str, Any]
    config: AgentCoreConfig | None
    validation_error: ValidationError | None


def read_toml(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        with open(path, "rb") as f:
            data = tomllib.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def load_project_config(path: Path) -> ConfigLoadResult:
    raw = read_toml(path)
    if not raw:
        return ConfigLoadResult(raw=raw, config=None, validation_error=None)

    try:
        config = AgentCoreConfig.model_validate(raw)
        return ConfigLoadResult(raw=raw, config=config, validation_error=None)
    except ValidationError as error:
        return ConfigLoadResult(raw=raw, config=None, validation_error=error)


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is None or origin is list or origin is dict:
        return annotation

    if origin is getattr(__import__("typing"), "Union", None) or str(origin) == "typing.Union":
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _is_model_type(annotation: Any) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(annotation, BaseModel)
    except Exception:
        return False


def _list_item_model_type(annotation: Any) -> type[BaseModel] | None:
    annotation = _unwrap_optional(annotation)
    if get_origin(annotation) is not list:
        return None
    args = get_args(annotation)
    if len(args) != 1:
        return None
    item_type = _unwrap_optional(args[0])
    if _is_model_type(item_type):
        return item_type
    return None


def _nested_model_type(annotation: Any) -> type[BaseModel] | None:
    annotation = _unwrap_optional(annotation)
    if _is_model_type(annotation):
        return annotation
    return None


def find_unknown_key_paths(raw: Any, model: type[BaseModel], prefix: str = "") -> list[str]:
    if not isinstance(raw, dict):
        return []

    allowed = set(model.model_fields.keys())
    unknown = [f"{prefix}{key}" for key in raw.keys() if key not in allowed]

    for field_name, field_info in model.model_fields.items():
        if field_name not in raw:
            continue

        value = raw[field_name]
        nested_model = _nested_model_type(field_info.annotation)
        if nested_model is not None:
            unknown.extend(find_unknown_key_paths(value, nested_model, f"{prefix}{field_name}."))
            continue

        item_model = _list_item_model_type(field_info.annotation)
        if item_model is None or not isinstance(value, list):
            continue

        for index, item in enumerate(value):
            if isinstance(item, dict):
                unknown.extend(
                    find_unknown_key_paths(item, item_model, f"{prefix}{field_name}[{index}].")
                )

    return unknown


def has_unknown_key_drift(raw: dict[str, Any]) -> bool:
    return len(find_unknown_key_paths(raw, AgentCoreConfig)) > 0


def summarize_validation_error(error: ValidationError, max_lines: int = 6) -> str:
    lines: list[str] = []
    for item in error.errors():
        loc = ".".join(str(part) for part in item.get("loc", []))
        message = item.get("msg", "Invalid value")
        lines.append(f"{loc}: {message}" if loc else message)
        if len(lines) >= max_lines:
            break

    if len(error.errors()) > max_lines:
        lines.append(f"... ({len(error.errors()) - max_lines} more)")
    return "\n".join(lines)


def _escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_multiline_string(value: str) -> str:
    return f'"""\n{value.strip()}\n"""'


def _description(model: type[BaseModel], field_name: str) -> str | None:
    field = model.model_fields.get(field_name)
    if field is None:
        return None
    return field.description


def generate_default_config_toml(
    project_name: str,
    project_description: str = "Add your project description here.",
    important_files: list[dict[str, str]] | None = None,
    tree_dirs: list[dict[str, str]] | None = None,
    symlink_paths: list[str] | None = None,
    main_branch: str = "main",
    test_branch: str = "test",
    noswitch_branches: dict[str, str] | None = None,
) -> str:
    if important_files is None:
        important_files = [
            {
                "path": "README.md",
                "description": "Project overview and setup instructions",
            }
        ]
    if symlink_paths is None:
        symlink_paths = WorktreeConfig().symlink_paths

    symlinks = ", ".join(f'"{path}"' for path in symlink_paths)

    lines = [
        "[project]",
        f"# {_description(ProjectConfig, 'name')}",
        f'name = "{_escape_toml_string(project_name)}"',
        "",
        f"# {_description(ProjectConfig, 'description')}",
        f"description = {_format_multiline_string(project_description)}",
        "",
        "# Files to include in onboard output",
    ]

    for item in important_files:
        lines.append("[[files]]")
        lines.append(f'path = "{_escape_toml_string(item["path"])}"')
        if item.get("description"):
            lines.append(f'description = "{_escape_toml_string(item["description"])}"')
        lines.append("")

    lines.append("# Directories whose tree structure is included in onboard output")
    if tree_dirs:
        for item in tree_dirs:
            lines.append("[[tree_dirs]]")
            lines.append(f'path = "{_escape_toml_string(item["path"])}"')
            if item.get("description"):
                lines.append(f'description = "{_escape_toml_string(item["description"])}"')
            lines.append("")
    else:
        lines.append('# [[tree_dirs]]')
        lines.append('# path = "src"')
        lines.append('# description = "Source code"')
        lines.append("")

    lines.extend(
        [
            "[worktree]",
            f"# {_description(WorktreeConfig, 'symlink_paths')}",
            f"symlink_paths = [{symlinks}]",
            "",
            "[branches]",
            f"# {_description(BranchConfig, 'main')}",
            f'main = "{_escape_toml_string(main_branch)}"',
            f"# {_description(BranchConfig, 'test')}",
            f'test = "{_escape_toml_string(test_branch)}"',
            f"# {_description(BranchConfig, 'noswitch_branches')}",
        ]
    )

    if noswitch_branches:
        lines.append("[branches.noswitch_branches]")
        for child, parent in noswitch_branches.items():
            lines.append(f'{_escape_toml_string(child)} = "{_escape_toml_string(parent)}"')
    else:
        lines.append("# [branches.noswitch_branches]")
        lines.append('# company_xyz = "main"')

    return "\n".join(lines) + "\n"
