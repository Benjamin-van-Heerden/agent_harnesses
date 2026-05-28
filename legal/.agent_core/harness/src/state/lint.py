from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths
from src.utils.markdown import frontmatter_get


def _missing_required(file: Path, key: str) -> str | None:
    if frontmatter_get(file, key):
        return None
    return f"{file}: missing required key '{key}'"


def _invalid_choice(file: Path, key: str, allowed: tuple[str, ...]) -> str | None:
    value = frontmatter_get(file, key)
    if not value or value in allowed:
        return None
    return f"{file}: '{key}' = '{value}' (allowed: {'|'.join(allowed)})"


def lint_frontmatter(paths: ProjectPaths = PROJECT_PATHS) -> list[str]:
    errors: list[str] = []

    for file in sorted(paths.clients_root.glob("*/profile.md")):
        for key in ("client_slug", "display_name", "client_type"):
            error = _missing_required(file, key)
            if error is not None:
                errors.append(error)
        error = _invalid_choice(file, "status", ("active", "resolved"))
        if error is not None:
            errors.append(error)

    matter_status_files = list(
        sorted(paths.clients_root.glob("*/matters/*/*/info/status.md"))
    )
    matter_status_files.extend(sorted(paths.unbound_root.glob("**/info/status.md")))
    for file in matter_status_files:
        for key in ("matter_type", "client", "billing"):
            error = _missing_required(file, key)
            if error is not None:
                errors.append(error)
        for key, allowed in (
            ("status", ("active", "on_hold", "resolved")),
            ("priority", ("low", "normal", "high", "urgent")),
        ):
            error = _invalid_choice(file, key, allowed)
            if error is not None:
                errors.append(error)

    if paths.src_functions_root.is_dir():
        errors.append(
            f"{paths.src_functions_root}: deprecated Typst layout; use src/components, src/templates, src/types, or src/constants"
        )
    nested_assets = paths.src_templates_root / "components" / "assets"
    if nested_assets.is_dir():
        errors.append(f"{nested_assets}: deprecated asset location; use root assets/")

    return errors
