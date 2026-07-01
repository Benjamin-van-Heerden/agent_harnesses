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


def test_sync_specs_skips_completed_local_spec_without_issue_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = _load_sync_module(monkeypatch, tmp_path)
    record = SimpleNamespace(
        slug="completed_spec",
        title="Completed Spec",
        body="Spec body",
        issue_id=None,
        status="completed",
        assigned_to="missing_user",
    )
    calls: list[tuple[str, Any]] = []

    monkeypatch.setattr(sync.specs, "list_all", lambda: [record])
    monkeypatch.setattr(sync, "list_issues", lambda repo, label, state: [])
    monkeypatch.setattr(sync, "create_issue", lambda *args, **kwargs: calls.append(("create", (args, kwargs))))

    assert sync._sync_specs(object(), authenticated_user="current_user") == 0
    assert calls == []


def test_sync_specs_validates_non_current_assignee_before_creating_issue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = _load_sync_module(monkeypatch, tmp_path)
    record = SimpleNamespace(
        slug="assigned_spec",
        title="Assigned Spec",
        body="Spec body",
        issue_id=None,
        status="todo",
        assigned_to="missing_user",
    )

    monkeypatch.setattr(sync.specs, "list_all", lambda: [record])
    monkeypatch.setattr(sync, "list_issues", lambda repo, label, state: [])
    monkeypatch.setattr(sync, "require_mapped_user", lambda username: (_ for _ in ()).throw(ValueError(f"missing mapping: {username}")))
    monkeypatch.setattr(sync, "create_issue", lambda *args, **kwargs: pytest.fail("issue creation must not run for an unmapped assignee"))

    with pytest.raises(ValueError, match="missing mapping: missing_user"):
        sync._sync_specs(object(), authenticated_user="current_user")


def test_sync_all_updates_current_user_mapping_after_issue_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sync = _load_sync_module(monkeypatch, tmp_path)
    calls: list[str] = []

    monkeypatch.setattr(sync, "sync_git_state", lambda: calls.append("git"))
    monkeypatch.setattr(sync, "status", lambda: calls.append("status"))
    monkeypatch.setattr(sync, "repository", lambda: "repo")
    monkeypatch.setattr(sync, "authenticated_username", lambda: calls.append("auth") or "current_user")
    monkeypatch.setattr(sync, "_sync_issues", lambda repo, authenticated_user: calls.append("issues") or 0)
    monkeypatch.setattr(sync, "ensure_current_user_mapping", lambda username: calls.append("mapping") or True)
    monkeypatch.setattr(sync, "_complete_merged_specs", lambda repo: (calls.append("complete"), 0)[1])
    monkeypatch.setattr(sync, "_cleanup_completed_spec_branches", lambda repo: (calls.append("cleanup"), 0)[1])
    monkeypatch.setattr(sync.git, "add_all", lambda: calls.append("add"))
    monkeypatch.setattr(sync.git, "commit", lambda message: (calls.append("commit"), False)[1])

    sync.sync_all(no_git=False)

    assert calls == ["git", "status", "auth", "issues", "mapping", "complete", "cleanup", "add", "commit"]
    output = capsys.readouterr().out
    assert "Updated managed file: .agent_core/user_mappings.toml" in output


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
