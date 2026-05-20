from pathlib import Path

from pydantic import BaseModel, ConfigDict

from src.models.frontmatter import (
    LogFrontmatter,
    MemoryFrontmatter,
    SpecFrontmatter,
    TaskFrontmatter,
    TodoFrontmatter,
)


class Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    path: Path
    body: str
    frontmatter: SpecFrontmatter

    @property
    def title(self) -> str:
        return self.frontmatter.title

    @property
    def status(self) -> str:
        return self.frontmatter.status

    @property
    def assigned_to(self) -> str | None:
        return self.frontmatter.assigned_to

    @property
    def issue_id(self) -> int | None:
        return self.frontmatter.issue_id

    @property
    def issue_url(self) -> str | None:
        return self.frontmatter.issue_url

    @property
    def branch(self) -> str | None:
        return self.frontmatter.branch

    @property
    def pr_url(self) -> str | None:
        return self.frontmatter.pr_url

    @property
    def created_at(self) -> str:
        return self.frontmatter.created_at

    @property
    def updated_at(self) -> str:
        return self.frontmatter.updated_at

    @property
    def completed_at(self) -> str | None:
        return self.frontmatter.completed_at


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    filename: str
    body: str
    frontmatter: TaskFrontmatter

    @property
    def title(self) -> str:
        return self.frontmatter.title

    @property
    def status(self) -> str:
        return self.frontmatter.status

    @property
    def created_at(self) -> str:
        return self.frontmatter.created_at

    @property
    def updated_at(self) -> str:
        return self.frontmatter.updated_at

    @property
    def completed_at(self) -> str | None:
        return self.frontmatter.completed_at


class Todo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    body: str
    frontmatter: TodoFrontmatter

    @property
    def title(self) -> str:
        return self.frontmatter.title

    @property
    def status(self) -> str:
        return self.frontmatter.status

    @property
    def issue_id(self) -> int | None:
        return self.frontmatter.issue_id

    @property
    def issue_url(self) -> str | None:
        return self.frontmatter.issue_url

    @property
    def created_at(self) -> str:
        return self.frontmatter.created_at

    @property
    def claimed_by(self) -> str | None:
        return self.frontmatter.claimed_by

    @property
    def claimed_at(self) -> str | None:
        return self.frontmatter.claimed_at


class Memory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    body: str
    frontmatter: MemoryFrontmatter

    @property
    def title(self) -> str:
        return self.frontmatter.title

    @property
    def created_at(self) -> str:
        return self.frontmatter.created_at

    @property
    def updated_at(self) -> str:
        return self.frontmatter.updated_at


class WorkLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    created_at: str
    date: str
    filename: str
    body: str
    frontmatter: LogFrontmatter

    @property
    def spec_slug(self) -> str | None:
        return self.frontmatter.spec_slug
