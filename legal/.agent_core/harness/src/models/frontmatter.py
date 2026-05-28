from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel


ClientStatus = Literal["active", "resolved"]
MatterStatusValue = Literal["active", "on_hold", "resolved"]
Priority = Literal["low", "normal", "high", "urgent"]
TodoStatus = Literal["open", "claimed"]
TodoPriority = Literal["low", "normal", "high"]


class ClientFrontmatter(BaseModel):
    client_slug: str
    display_name: str
    client_type: str
    opened: str
    status: ClientStatus = "active"

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class MatterStatusFrontmatter(BaseModel):
    matter_type: str
    status: MatterStatusValue = "active"
    priority: Priority = "normal"
    opened: str
    client: str
    workspace: str = "client"
    unbound_path: str | None = None
    bound_from: str | None = None
    co_clients: list[str] = []
    opposing_parties: list[str] = []
    court: str | None = None
    case_number: str | None = None
    physical_files: list[str] = []
    workflow: str | None = None
    last_touched_at: str | None = None
    next_obligation: str | None = None
    billing: str
    tags: list[str] = []

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class TodoFrontmatter(BaseModel):
    slug: str
    created: str
    status: TodoStatus = "open"
    priority: TodoPriority = "normal"
    matter: str | None = None
    obligation: str | None = None
    claimed_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class MemoryFrontmatter(BaseModel):
    slug: str
    created: str
    tags: list[str] = []

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()


class WorkLogFrontmatter(BaseModel):
    date: str
    session_start: str
    matter: str | None = None

    def to_dict(self) -> Mapping[str, object]:
        return self.model_dump()
