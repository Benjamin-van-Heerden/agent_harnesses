import importlib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from helpers import HARNESS_ROOT


@dataclass(frozen=True)
class FakeLabel:
    name: str


@dataclass(frozen=True)
class FakeIssue:
    number: int
    title: str
    body: str
    labels: list[FakeLabel]
    state: str = "open"
    html_url: str = "https://example.test/issues/1"
    pull_request: None = None


def _load_sync_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    monkeypatch.chdir(tmp_path)
    return importlib.import_module("src.commands.sync.main")


def test_sync_specs_does_not_update_matching_remote_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = _load_sync_module(monkeypatch, tmp_path)
    record = SimpleNamespace(
        slug="synced_spec",
        title="Synced Spec",
        body="Spec body",
        issue_id=1,
        status="todo",
        assigned_to=None,
    )
    issue = FakeIssue(
        number=1,
        title="Synced Spec",
        body="Spec body",
        labels=[FakeLabel("spec"), FakeLabel("status:todo")],
    )
    calls: list[tuple[str, Any]] = []

    monkeypatch.setattr(sync.specs, "list_all", lambda: [record])
    monkeypatch.setattr(sync, "list_issues", lambda repo, label, state: [issue])
    monkeypatch.setattr(sync, "update_issue", lambda *args, **kwargs: calls.append(("update", (args, kwargs))))

    assert sync._sync_specs(object()) == 0
    assert calls == []


def test_sync_todos_updates_mismatched_remote_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = _load_sync_module(monkeypatch, tmp_path)
    record = SimpleNamespace(
        slug="open_todo",
        title="Open Todo",
        body="Todo body",
        issue_id=2,
        status="open",
    )
    issue = FakeIssue(
        number=2,
        title="Open Todo",
        body="Stale body",
        labels=[FakeLabel("todo"), FakeLabel("status:todo")],
    )
    calls: list[tuple[str, Any]] = []

    monkeypatch.setattr(sync.todos, "list_all", lambda: [record])
    monkeypatch.setattr(sync, "list_issues", lambda repo, label, state: [issue])
    monkeypatch.setattr(sync, "update_issue", lambda *args, **kwargs: calls.append(("update", (args, kwargs))))

    assert sync._sync_todos(object()) == 1
    assert len(calls) == 1
