from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    description: str


@dataclass(frozen=True)
class HarnessConfig:
    name: str
    local_git_snapshots: bool
    last_updated_at: str
    update_interval_days: int


@dataclass(frozen=True)
class LegalConfig:
    jurisdiction: str


@dataclass(frozen=True)
class LegalHarnessConfig:
    project: ProjectConfig
    harness: HarnessConfig
    legal: LegalConfig
