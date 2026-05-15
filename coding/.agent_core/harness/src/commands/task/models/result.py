from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class TaskCommandResult(BaseModel):
    slug: str
    path: Path
