from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, client_dir, client_profile
from src.state.models import ClientProfile
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_slug
from src.utils.markdown import read_markdown


def parse_client_profile(path: Path) -> ClientProfile:
    document = read_markdown(path)
    return ClientProfile(
        client_slug=document.frontmatter.get("client_slug", ""),
        display_name=document.frontmatter.get("display_name", ""),
        client_type=document.frontmatter.get("client_type", ""),
        opened=document.frontmatter.get("opened", ""),
        status=document.frontmatter.get("status", ""),
        path=path,
    )


def resolve_client(slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_slug(slug)
    path = client_dir(slug, paths)
    if not path.is_dir():
        raise FileNotFoundError(f"client not found: {slug}")
    return path


def list_clients(paths: ProjectPaths = PROJECT_PATHS) -> list[ClientProfile]:
    if not paths.clients_root.is_dir():
        return []
    profiles: list[ClientProfile] = []
    for path in sorted(paths.clients_root.glob("*/profile.md")):
        profiles.append(parse_client_profile(path))
    return profiles


def create_client(slug: str, display_name: str, client_type: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    validate_slug(slug)
    path = client_dir(slug, paths)
    if path.exists():
        raise FileExistsError(f"client already exists: {slug}")

    (path / "matters" / "open").mkdir(parents=True, exist_ok=True)
    (path / "matters" / "resolved").mkdir(parents=True, exist_ok=True)

    profile = client_profile(slug, paths)
    profile.write_text(
        render_template(
            "profile",
            paths,
            CLIENT_SLUG=slug,
            DISPLAY_NAME=display_name,
            CLIENT_TYPE=client_type,
            TODAY=today(),
        )
    )
    return profile
