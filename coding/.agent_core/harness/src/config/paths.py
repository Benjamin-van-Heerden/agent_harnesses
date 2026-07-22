from dataclasses import dataclass
from pathlib import Path


STATE_DIR_NAME = ".agent_core"
HARNESS_DIR_NAME = "harness"


@dataclass(frozen=True)
class ProjectPaths:
    @property
    def project_root(self) -> Path:
        return Path.cwd()

    @property
    def state_root(self) -> Path:
        return self.project_root / STATE_DIR_NAME

    @property
    def state_root_display(self) -> str:
        return f"{STATE_DIR_NAME}/"

    @property
    def harness_root(self) -> Path:
        return self.state_root / HARNESS_DIR_NAME

    @property
    def harness_root_display(self) -> str:
        return f"{STATE_DIR_NAME}/{HARNESS_DIR_NAME}/"

    @property
    def config_file(self) -> Path:
        return self.state_root / "config.toml"

    @property
    def config_file_display(self) -> str:
        return f"{STATE_DIR_NAME}/config.toml"

    @property
    def user_mappings_file(self) -> Path:
        return self.state_root / "user_mappings.toml"

    @property
    def user_mappings_file_display(self) -> str:
        return f"{STATE_DIR_NAME}/user_mappings.toml"

    @property
    def specs_dir(self) -> Path:
        return self.state_root / "specs"

    @property
    def todos_dir(self) -> Path:
        return self.state_root / "todos"

    @property
    def memories_dir(self) -> Path:
        return self.state_root / "memories"

    @property
    def logs_dir(self) -> Path:
        return self.state_root / "logs"

    @property
    def docs_dir(self) -> Path:
        return self.state_root / "docs"

    @property
    def optional_docs_file(self) -> Path:
        return self.state_root / "optional_docs.toml"

    @property
    def optional_docs_catalog_dir(self) -> Path:
        return self.harness_root / "optional_docs"


PROJECT_PATHS = ProjectPaths()
