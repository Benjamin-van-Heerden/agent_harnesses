from pathlib import Path

from pydantic import BaseModel


class SpecCommandResult(BaseModel):
    slug: str
    path: Path
