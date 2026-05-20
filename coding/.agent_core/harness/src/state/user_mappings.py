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


def load_all() -> dict[str, UserMapping]:
    if not PROJECT_PATHS.user_mappings_file.exists():
        return {}

    with open(PROJECT_PATHS.user_mappings_file, "rb") as f:
        return USER_MAPPINGS_ADAPTER.validate_python(tomllib.load(f))


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
