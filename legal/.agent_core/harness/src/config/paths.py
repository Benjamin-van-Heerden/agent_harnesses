from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    project_root: Path
    state_root: Path
    harness_root: Path
    config_file: Path
    core_docs_root: Path
    docs_root: Path
    legal_context: Path
    client_matter_index: Path
    workflows_root: Path
    typst_basic_reference: Path
    typst_house_rules_reference: Path
    typst_detailed_reference: Path
    local_context_root: Path
    lawyer_profile: Path
    firm_profile: Path
    clients_root: Path
    wip_root: Path
    wip_drafts_root: Path
    wip_experiments_root: Path
    memories_root: Path
    logs_root: Path
    global_todos_root: Path
    global_open_todos_root: Path
    global_claimed_todos_root: Path
    templates_root: Path
    src_root: Path
    src_types_root: Path
    src_constants_root: Path
    src_functions_root: Path
    src_templates_root: Path
    legacy_functions_root: Path
    legacy_templates_root: Path


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".praxis").is_dir():
            return candidate
    return current


def build_project_paths(project_root: Path | None = None) -> ProjectPaths:
    root = (project_root or find_project_root()).resolve()
    state_root = root / ".praxis"
    harness_root = state_root / "harness"
    core_docs_root = state_root / "core_docs"
    docs_root = state_root / "docs"
    local_context_root = state_root / "local_context"
    return ProjectPaths(
        project_root=root,
        state_root=state_root,
        harness_root=harness_root,
        config_file=state_root / "config.toml",
        core_docs_root=core_docs_root,
        docs_root=docs_root,
        legal_context=core_docs_root / "legal_context.typ",
        client_matter_index=state_root / "client_matter_index.toml",
        workflows_root=local_context_root / "workflows",
        typst_basic_reference=docs_root / "legal_harness_typst_basic_reference.typ",
        typst_house_rules_reference=docs_root / "legal_harness_typst_soft_typesystem_and_house_rules.typ",
        typst_detailed_reference=docs_root / "typst_detailed_reference.typ",
        local_context_root=local_context_root,
        lawyer_profile=local_context_root / "lawyer_profile.md",
        firm_profile=local_context_root / "firm_profile.md",
        clients_root=root / "ZZ_CLIENTS",
        wip_root=root / "WIP",
        wip_drafts_root=root / "WIP" / "drafts",
        wip_experiments_root=root / "WIP" / "experiments",
        memories_root=local_context_root / "memories",
        logs_root=local_context_root / "logs",
        global_todos_root=state_root / "todos",
        global_open_todos_root=state_root / "todos" / "open",
        global_claimed_todos_root=state_root / "todos" / "claimed",
        templates_root=harness_root / "templates",
        src_root=root / "src",
        src_types_root=root / "src" / "types",
        src_constants_root=root / "src" / "constants",
        src_functions_root=root / "src" / "functions",
        src_templates_root=root / "src" / "templates",
        legacy_functions_root=root / "functions",
        legacy_templates_root=root / "templates",
    )


PROJECT_PATHS = build_project_paths()


def client_dir(client_slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    return paths.clients_root / client_slug


def client_profile(client_slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    return client_dir(client_slug, paths) / "profile.md"


def matter_bucket(client_slug: str, status: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    return client_dir(client_slug, paths) / "matters" / status


def matter_dir(client_slug: str, status: str, matter_slug: str, paths: ProjectPaths = PROJECT_PATHS) -> Path:
    return matter_bucket(client_slug, status, paths) / matter_slug


def matter_info_dir(matter_path: Path) -> Path:
    return matter_path / "info"


def matter_status_file(matter_path: Path) -> Path:
    return matter_info_dir(matter_path) / "status.md"


def matter_chronology_dir(matter_path: Path) -> Path:
    return matter_info_dir(matter_path) / "chronology"


def matter_obligations_dir(matter_path: Path) -> Path:
    return matter_info_dir(matter_path) / "obligations"


def matter_todos_dir(matter_path: Path) -> Path:
    return matter_info_dir(matter_path) / "todos"


def matter_workflow_progress_file(matter_path: Path) -> Path:
    return matter_info_dir(matter_path) / "workflow.toml"


def matter_raw_dir(matter_path: Path) -> Path:
    return matter_path / "raw"


def matter_reference_dir(matter_path: Path) -> Path:
    return matter_path / "reference"
