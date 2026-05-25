import re
import unicodedata
from pathlib import Path

from src.config.paths import PROJECT_PATHS, ProjectPaths, client_dir, client_profile
from src.models.frontmatter import ClientFrontmatter
from src.state.models import ClientProfile
from src.state.templates import render_template
from src.state.time import today
from src.state.validation import validate_slug
from src.utils.markdown import MarkdownDocument, frontmatter_get, write_markdown


NON_SLUG_TEXT_RE = re.compile(r"[^a-z0-9]+")


def slugify_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = NON_SLUG_TEXT_RE.sub("_", ascii_text.lower()).strip("_")
    if not slug:
        raise ValueError(f"cannot generate a slug from '{value}'")
    validate_slug(slug)
    return slug


def natural_person_slug(display_name: str, suffix: str = "") -> str:
    surname, separator, given_names = display_name.partition(",")
    if not separator or not surname.strip() or not given_names.strip():
        raise ValueError(
            "natural person client names must be surname-first, for example 'Van Heerden, Benjamin'"
        )
    parts = [slugify_text(surname), slugify_text(given_names)]
    if suffix:
        parts.append(slugify_text(suffix))
    return "_".join(parts)


def entity_slug(display_name: str, suffix: str = "") -> str:
    parts = [slugify_text(display_name)]
    if suffix:
        parts.append(slugify_text(suffix))
    return "_".join(parts)


def generated_client_slug(display_name: str, client_type: str, suffix: str = "") -> str:
    if client_type == "person":
        return natural_person_slug(display_name, suffix)
    return entity_slug(display_name, suffix)


def collision_message(slug: str) -> str:
    return (
        f"client already exists: {slug}. Ask the lawyer for a distinguishing suffix such as location, ID hint, company, or role, then rerun client creation with that suffix."
    )


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
        raise FileExistsError(collision_message(slug))

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


def create_client_from_name(
    display_name: str,
    client_type: str,
    suffix: str = "",
    explicit_slug: str = "",
    paths: ProjectPaths = PROJECT_PATHS,
) -> Path:
    slug = explicit_slug or generated_client_slug(display_name, client_type, suffix)
    return create_client(slug, display_name, client_type, paths)
