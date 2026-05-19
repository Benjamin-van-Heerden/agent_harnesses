from collections.abc import Mapping
from dataclasses import dataclass, field

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Project name displayed in onboard context")
    description: str = Field(
        default="Add your project description here.",
        description="Project description for onboarding context",
    )


class ImportantFileConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str = Field(..., description="Path to file relative to project root")
    description: str | None = Field(default=None, description="Why this file matters")


class TreeDirConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str = Field(..., description="Path to directory relative to project root")
    description: str | None = Field(default=None, description="Why this directory matters")


class WorktreeConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    symlink_paths: list[str] = Field(
        default=[".agent_core/docs/data", ".claude"],
        description="Paths to symlink into worktrees instead of copying",
    )


class HarnessConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    last_updated_at: str | None = Field(
        default=None,
        description="Last successful harness update timestamp",
    )
    update_interval_days: int = Field(
        default=3,
        ge=0,
        description="Number of days before onboard checks for a harness update",
    )


class NoSwitchBranch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    child: str
    parent: str


class NoSwitchBranches(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: tuple[NoSwitchBranch, ...] = Field(default_factory=tuple)

    @model_validator(mode="before")
    @classmethod
    def parse_toml_mapping(cls, value: object) -> object:
        if isinstance(value, Mapping):
            return {
                "entries": tuple(
                    NoSwitchBranch(child=str(child), parent=str(parent))
                    for child, parent in value.items()
                )
            }
        return value

    def parent_for(self, child: str | None) -> str | None:
        if child is None:
            return None
        for entry in self.entries:
            if entry.child == child:
                return entry.parent
        return None

    def has_child(self, child: str | None) -> bool:
        return self.parent_for(child) is not None

    def as_toml_items(self) -> tuple[NoSwitchBranch, ...]:
        return self.entries


class BranchConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dev: str = Field(..., description="Development branch")
    test: str = Field(..., description="Staging branch")
    main: str = Field(..., description="Production branch")
    noswitch_branches: NoSwitchBranches = Field(
        default_factory=NoSwitchBranches,
        description="Branches that should not auto-switch to dev",
    )


class AgentCoreConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project: ProjectConfig
    files: list[ImportantFileConfig] = Field(default_factory=list)
    tree_dirs: list[TreeDirConfig] = Field(default_factory=list)
    worktree: WorktreeConfig = Field(default_factory=WorktreeConfig)
    harness: HarnessConfig = Field(default_factory=HarnessConfig)
    branches: BranchConfig


@dataclass(frozen=True)
class BranchNames:
    dev: str
    test: str
    main: str
    noswitch_branches: NoSwitchBranches = field(default_factory=NoSwitchBranches)

    @property
    def protected(self) -> list[str]:
        return [self.dev, self.test, self.main]
