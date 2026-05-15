from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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


class BranchConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    main: str = Field(default="main", description="Production branch")
    test: str = Field(default="test", description="Staging branch")
    noswitch_branches: dict[str, str] = Field(
        default_factory=dict,
        description="Branches that should not auto-switch to dev",
    )


class AgentCoreConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project: ProjectConfig
    files: list[ImportantFileConfig] = Field(default_factory=list)
    tree_dirs: list[TreeDirConfig] = Field(default_factory=list)
    worktree: WorktreeConfig = Field(default_factory=WorktreeConfig)
    branches: BranchConfig = Field(default_factory=BranchConfig)


@dataclass(frozen=True)
class BranchNames:
    dev: str
    test: str
    main: str
    noswitch_branches: dict[str, str] = field(default_factory=dict)

    @property
    def protected(self) -> list[str]:
        return [self.dev, self.test, self.main]


def get_model_field_names(model: type[BaseModel]) -> set[str]:
    return set(model.model_fields.keys())


def is_known_freeform_mapping_type(annotation: Any) -> bool:
    _ = annotation
    return False
