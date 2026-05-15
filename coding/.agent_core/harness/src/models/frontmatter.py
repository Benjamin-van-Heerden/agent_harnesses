from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


SpecStatus = Literal["todo", "merge_ready", "completed", "abandoned"]
TaskStatus = Literal["todo", "completed"]
TodoStatus = Literal["open", "claimed"]


def _iso_string(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class SpecFrontmatter(BaseModel):
    title: str
    status: SpecStatus = "todo"
    assigned_to: str | None = None
    issue_id: int | None = None
    issue_url: str | None = None
    branch: str | None = None
    pr_url: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None
    last_synced_at: str | None = None
    local_content_hash: str | None = None
    remote_content_hash: str | None = None

    @field_validator("created_at", "updated_at", "completed_at", mode="before")
    @classmethod
    def normalize_datetime(cls, value: object) -> object:
        return _iso_string(value)

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class TaskFrontmatter(BaseModel):
    title: str
    status: TaskStatus = "todo"
    created_at: str
    updated_at: str
    completed_at: str | None = None

    @field_validator("created_at", "updated_at", "completed_at", mode="before")
    @classmethod
    def normalize_datetime(cls, value: object) -> object:
        return _iso_string(value)

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class TodoFrontmatter(BaseModel):
    title: str
    status: TodoStatus = "open"
    issue_id: int | None = None
    issue_url: str | None = None
    created_at: str
    claimed_by: str | None = None
    claimed_at: str | None = None

    @field_validator("created_at", "claimed_at", mode="before")
    @classmethod
    def normalize_datetime(cls, value: object) -> object:
        return _iso_string(value)

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class MemoryFrontmatter(BaseModel):
    title: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def normalize_datetime(cls, value: object) -> object:
        return _iso_string(value)

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class LogFrontmatter(BaseModel):
    created_at: str
    username: str
    spec_slug: str | None = None

    @field_validator("created_at", mode="before")
    @classmethod
    def normalize_datetime(cls, value: object) -> object:
        return _iso_string(value)

    def to_dict(self) -> Mapping[str, object]:
        return {key: value for key, value in self.model_dump().items() if value is not None}


def now_iso() -> str:
    return datetime.now().isoformat()


def create_spec_frontmatter(
    title: str,
    status: SpecStatus = "todo",
    assigned_to: str | None = None,
    issue_id: int | None = None,
    issue_url: str | None = None,
    branch: str | None = None,
    pr_url: str | None = None,
) -> SpecFrontmatter:
    now = now_iso()
    return SpecFrontmatter(
        title=title,
        status=status,
        assigned_to=assigned_to,
        issue_id=issue_id,
        issue_url=issue_url,
        branch=branch,
        pr_url=pr_url,
        created_at=now,
        updated_at=now,
    )


def create_task_frontmatter(title: str, status: TaskStatus = "todo") -> TaskFrontmatter:
    now = now_iso()
    return TaskFrontmatter(title=title, status=status, created_at=now, updated_at=now)


def create_todo_frontmatter(
    title: str,
    issue_id: int | None = None,
    issue_url: str | None = None,
) -> TodoFrontmatter:
    return TodoFrontmatter(
        title=title,
        issue_id=issue_id,
        issue_url=issue_url,
        created_at=now_iso(),
    )


def create_memory_frontmatter(title: str) -> MemoryFrontmatter:
    now = now_iso()
    return MemoryFrontmatter(title=title, created_at=now, updated_at=now)


def create_log_frontmatter(
    created_at: datetime,
    username: str,
    spec_slug: str | None = None,
) -> LogFrontmatter:
    return LogFrontmatter(
        created_at=created_at.isoformat(),
        username=username,
        spec_slug=spec_slug,
    )
