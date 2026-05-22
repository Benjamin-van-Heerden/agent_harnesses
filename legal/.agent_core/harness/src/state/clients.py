from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, client_dir, client_profile
from src.models.frontmatter import ClientFrontmatter
from src.state.models import ClientProfile
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_slug
from src.utils.markdown import MarkdownDocument, frontmatter_get, write_markdown


def parse_client_profile(path: Path) -> ClientProfile:
    return ClientProfile(
        client_slug=frontmatter_get(path, "client_slug"),
        display_name=frontmatter_get(path, "display_name"),
        client_type=frontmatter_get(path, "client_type"),
        opened=frontmatter_get(path, "opened"),
        status=frontmatter_get(path, "status"),
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
    body = render_template("profile", paths)
    write_markdown(
        profile,
        MarkdownDocument(
            frontmatter=ClientFrontmatter(
                client_slug=slug,
                display_name=display_name,
                client_type=client_type,
                opened=today(),
            ).to_dict(),
            body=body,
        ),
    )
    return profile
