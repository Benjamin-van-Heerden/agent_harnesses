from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from github_helpers import client_for_token, prepare_remote_project, token_or_skip


@dataclass(frozen=True)
class RemoteHarnessProject:
    path: Path
    repo: object
    token: str = field(repr=False)


@pytest.fixture
def remote_harness_project(tmp_path):
    token = token_or_skip()
    client = client_for_token(token)
    project_path = tmp_path / "project"
    repo = prepare_remote_project(project_path, token, client)
    return RemoteHarnessProject(project_path, repo, token)
