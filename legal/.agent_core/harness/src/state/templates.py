from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths


def template_path(name: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    return paths.templates_root / f"{name}.md"


def render_template(name: str, paths: ProjectPaths = PROJECT_PATHS, **values: str) -> str:
    path = template_path(name, paths)
    if not path.is_file():
        raise FileNotFoundError(f"template not found: {path}")

    content = path.read_text()
    for key, value in values.items():
        content = content.replace(f"${key}", value)
    if not content.endswith("\n"):
        content += "\n"
    return content


def ensure_file_from_template(path: Path, template_name: str, paths: ProjectPaths = PROJECT_PATHS) -> None:
    if path.is_file():
        return
    source = template_path(template_name, paths)
    if not source.is_file():
        raise FileNotFoundError(f"template not found: {source}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source.read_bytes())
