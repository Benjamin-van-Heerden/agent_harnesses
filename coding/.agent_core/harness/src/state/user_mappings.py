import json
import subprocess
import tomllib

from pydantic import BaseModel, ConfigDict, TypeAdapter

from src.config.paths import PROJECT_PATHS
from src.utils.markdown import slugify


class UserMapping(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    email: str | None = None


USER_MAPPINGS_ADAPTER = TypeAdapter(dict[str, UserMapping])


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _coerce_mappings(data: dict[str, object]) -> dict[str, UserMapping]:
    mappings: dict[str, UserMapping] = {}
    for username, value in data.items():
        if isinstance(value, str):
            mappings[username] = UserMapping(name=value)
            continue
        mappings[username] = UserMapping.model_validate(value)
    return mappings


def _render_mappings(mappings: dict[str, UserMapping]) -> str:
    lines = ["# GitHub username to git user mappings"]
    for username, mapping in sorted(mappings.items()):
        lines.append("")
        lines.append(f"[{username}]")
        lines.append(f"name = {_toml_string(mapping.name)}")
        if mapping.email:
            lines.append(f"email = {_toml_string(mapping.email)}")
    return "\n".join(lines).rstrip() + "\n"


def ensure_user_mappings_file() -> bool:
    if not PROJECT_PATHS.user_mappings_file.exists():
        PROJECT_PATHS.user_mappings_file.write_text("# GitHub username to git user mappings\n")
        return True

    with open(PROJECT_PATHS.user_mappings_file, "rb") as f:
        raw = tomllib.load(f)
    if not any(isinstance(value, str) for value in raw.values()):
        return False

    PROJECT_PATHS.user_mappings_file.write_text(_render_mappings(_coerce_mappings(raw)))
    return True


def load_all() -> dict[str, UserMapping]:
    if not PROJECT_PATHS.user_mappings_file.exists():
        return {}

    with open(PROJECT_PATHS.user_mappings_file, "rb") as f:
        raw = tomllib.load(f)
    if any(isinstance(value, str) for value in raw.values()):
        return _coerce_mappings(raw)
    return USER_MAPPINGS_ADAPTER.validate_python(raw)


def require_mapped_user(username: str) -> UserMapping:
    mapping = load_all().get(username)
    if mapping is None:
        raise ValueError(
            f"GitHub user '{username}' is not mapped in {PROJECT_PATHS.user_mappings_file_display}. "
            f"Add a [{username}] section before assigning specs to that user."
        )
    return mapping


def _git_user_name() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            cwd=PROJECT_PATHS.project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def current_username() -> str:
    git_name = _git_user_name()
    try:
        mappings = load_all()
    except Exception:
        mappings = {}

    for username, details in mappings.items():
        if details.name == git_name:
            return slugify(username)

    return slugify(git_name)
