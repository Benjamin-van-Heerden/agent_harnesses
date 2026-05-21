import subprocess
from pathlib import Path
from types import ModuleType

import pytest
import typer

from helpers import HARNESS_ROOT, init_git_project, install_harness, read_frontmatter


def _load_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


def _prepare_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    monkeypatch.chdir(target)
    return target


def _create_synced_spec(specs: ModuleType, title: str) -> str:
    path = specs.create(title, body="Spec body")
    slug = path.parent.name
    specs.update_issue(slug, 123, "https://github.example/spec/123")
    return slug


def _patch_assignment_boundaries(
    assign: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    username: str = "current_user",
) -> list[tuple[str, object]]:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(assign.git, "fetch", lambda: calls.append(("fetch", None)))
    monkeypatch.setattr(assign.git, "remote_branch_exists", lambda branch: True)
    monkeypatch.setattr(assign.git, "local_ahead_of_remote", lambda branch: False)
    monkeypatch.setattr(assign.git, "remote_ahead_of_local", lambda branch: False)
    monkeypatch.setattr(assign.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(assign.git, "add_all", lambda: calls.append(("add_all", None)))
    monkeypatch.setattr(assign.git, "commit", lambda message: calls.append(("commit", message)) or True)
    monkeypatch.setattr(assign.git, "push", lambda branch, cwd=None, set_upstream=False: calls.append(("push", (branch, cwd, set_upstream))))
    monkeypatch.setattr(assign.git, "push_ref", lambda source, branch: calls.append(("push_ref", (source, branch))))
    monkeypatch.setattr(assign.worktrees, "is_worktree", lambda: False)
    monkeypatch.setattr(assign.worktrees, "list_all", lambda: [])
    monkeypatch.setattr(assign, "authenticated_username", lambda: username)
    monkeypatch.setattr(assign, "repository", lambda: object())
    monkeypatch.setattr(assign, "update_issue", lambda repo, issue_id, *, assignees: calls.append(("update_issue", (issue_id, assignees))))
    return calls


def test_spec_assign_current_user_still_creates_local_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _prepare_project(tmp_path, monkeypatch)
    specs = _load_module(monkeypatch, "src.state.specs")
    assign = _load_module(monkeypatch, "src.commands.spec.assign")
    slug = _create_synced_spec(specs, "Current Assignment")
    calls = _patch_assignment_boundaries(assign, monkeypatch, username="current_user")
    worktree_path = tmp_path / "project-worktrees" / slug

    def create_worktree(create_slug: str, branch: str) -> Path:
        calls.append(("create_worktree", (create_slug, branch)))
        worktree_path.mkdir(parents=True)
        return worktree_path

    monkeypatch.setattr(assign.worktrees, "path_for", lambda create_slug: tmp_path / "project-worktrees" / create_slug)
    monkeypatch.setattr(assign.worktrees, "create", create_worktree)

    assign.run(slug)

    metadata = read_frontmatter(target / ".agent_core" / "specs" / slug / "spec.md")
    expected_branch = f"dev-current_user-{slug}"
    assert metadata["assigned_to"] == "current_user"
    assert metadata["branch"] == expected_branch
    assert ("create_worktree", (slug, expected_branch)) in calls
    assert ("push", (expected_branch, worktree_path, True)) in calls
    assert ("update_issue", (123, ["current_user"])) in calls
    output = capsys.readouterr().out
    assert "Assigned spec to authenticated GitHub user." in output
    assert "Created worktree:" in output
    assert "WORKTREE READY - START NEW SESSION" in output


def test_spec_assign_explicit_mapped_assignee_pushes_remote_branch_without_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = _prepare_project(tmp_path, monkeypatch)
    (target / ".agent_core" / "user_mappings.toml").write_text(
        '[remote_user]\nname = "Remote User"\nemail = "remote@example.com"\n'
    )
    specs = _load_module(monkeypatch, "src.state.specs")
    assign = _load_module(monkeypatch, "src.commands.spec.assign")
    slug = _create_synced_spec(specs, "Remote Assignment")
    calls = _patch_assignment_boundaries(assign, monkeypatch, username="current_user")
    monkeypatch.setattr(assign.worktrees, "create", lambda create_slug, branch: pytest.fail("remote assignment must not create a worktree"))

    assign.run(slug, assignee="remote_user")

    metadata = read_frontmatter(target / ".agent_core" / "specs" / slug / "spec.md")
    expected_branch = f"dev-remote_user-{slug}"
    assert metadata["assigned_to"] == "remote_user"
    assert metadata["branch"] == expected_branch
    assert ("push_ref", ("HEAD", expected_branch)) in calls
    assert ("update_issue", (123, ["remote_user"])) in calls
    output = capsys.readouterr().out
    assert "Assigned spec to mapped GitHub user." in output
    assert "No local worktree was created for the current user." in output
    assert "The assignee will receive the worktree when they run onboard." in output


def test_spec_assign_explicit_assignee_requires_user_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_project(tmp_path, monkeypatch)
    specs = _load_module(monkeypatch, "src.state.specs")
    assign = _load_module(monkeypatch, "src.commands.spec.assign")
    slug = _create_synced_spec(specs, "Unknown Assignment")
    _patch_assignment_boundaries(assign, monkeypatch, username="current_user")

    with pytest.raises(typer.Exit):
        assign.run(slug, assignee="missing_user")

    error_output = capsys.readouterr().err
    assert "GitHub user 'missing_user' is not mapped in .agent_core/user_mappings.toml." in error_output
    assert "Add a [missing_user] section before assigning specs to that user." in error_output


def test_onboard_assigned_worktree_creation_uses_recorded_remote_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_project(tmp_path, monkeypatch)
    specs = _load_module(monkeypatch, "src.state.specs")
    assigned_worktrees = _load_module(monkeypatch, "src.commands.onboard.assigned_worktrees")
    slug = _create_synced_spec(specs, "Assigned Onboard")
    specs.update_assignment(slug, "current_user")
    specs.update_branch(slug, f"dev-current_user-{slug}")
    calls: list[tuple[str, object]] = []
    created_path = tmp_path / "project-worktrees" / slug

    monkeypatch.setattr(assigned_worktrees, "authenticated_username", lambda: "current_user")
    monkeypatch.setattr(assigned_worktrees.worktrees, "is_worktree", lambda: False)
    monkeypatch.setattr(assigned_worktrees.worktrees, "list_all", lambda: [])
    monkeypatch.setattr(assigned_worktrees.git, "fetch", lambda: calls.append(("fetch", None)))
    monkeypatch.setattr(assigned_worktrees.git, "remote_branch_exists", lambda branch: True)
    monkeypatch.setattr(
        assigned_worktrees.worktrees,
        "create_from_remote",
        lambda create_slug, branch: calls.append(("create_from_remote", (create_slug, branch))) or created_path,
    )

    results = assigned_worktrees.create_missing_for_authenticated_user()

    expected_branch = f"dev-current_user-{slug}"
    assert calls == [("fetch", None), ("create_from_remote", (slug, expected_branch))]
    assert len(results) == 1
    assert results[0].spec_slug == slug
    assert results[0].branch == expected_branch
    assert results[0].path == created_path


def test_worktree_create_from_remote_tracks_origin_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worktrees = _load_module(monkeypatch, "src.utils.worktrees")
    calls: list[list[str]] = []

    def run_git(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        if args[:2] == ["branch", "--list"]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(worktrees, "run_git", run_git)
    monkeypatch.setattr(worktrees, "_create_configured_symlinks", lambda main_repo_path, worktree_path: [])

    result = worktrees.create_from_remote("remote_slug", "dev-remote_user-remote_slug", tmp_path / "project")

    assert result == tmp_path / "project-worktrees" / "remote_slug"
    assert [
        "worktree",
        "add",
        "--track",
        "-b",
        "dev-remote_user-remote_slug",
        str(tmp_path / "project-worktrees" / "remote_slug"),
        "origin/dev-remote_user-remote_slug",
    ] in calls


def test_spec_new_stdout_distinguishes_assignment_modes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare_project(tmp_path, monkeypatch)
    new = _load_module(monkeypatch, "src.commands.spec.new")
    monkeypatch.setattr(new.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(new.worktrees, "is_worktree", lambda: False)

    new.run("Guidance Spec", body="Guidance body")

    output = capsys.readouterr().out
    assert "Current user:" in output
    assert "assigns it to the authenticated GitHub user and creates a local worktree" in output
    assert "Another user:" in output
    assert "--assignee <github_username>" in output
    assert "creates no local worktree for the current user" in output


def test_spec_create_suffixes_duplicate_slugs_across_status_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_project(tmp_path, monkeypatch)
    specs = _load_module(monkeypatch, "src.state.specs")

    first = specs.create("Duplicate Spec", body="First")
    first_slug = first.parent.name
    specs.update_status(first_slug, "completed")
    second = specs.create("Duplicate Spec", body="Second")
    third = specs.create("Duplicate Spec", body="Third")

    assert first_slug == "duplicate_spec"
    assert second.parent.name == "duplicate_spec_2"
    assert third.parent.name == "duplicate_spec_3"
    assert (tmp_path / "project" / ".agent_core" / "specs" / "completed" / "duplicate_spec" / "spec.md").is_file()
    assert (tmp_path / "project" / ".agent_core" / "specs" / "duplicate_spec_2" / "spec.md").is_file()
    assert (tmp_path / "project" / ".agent_core" / "specs" / "duplicate_spec_3" / "spec.md").is_file()


def test_spec_status_move_preserves_additional_spec_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _prepare_project(tmp_path, monkeypatch)
    specs = _load_module(monkeypatch, "src.state.specs")

    spec_path = specs.create("Research Spec", body="Spec body")
    spec_dir = spec_path.parent
    (spec_dir / "legal_migration_research.md").write_text("Research notes\n")
    (spec_dir / "tasks").mkdir()
    (spec_dir / "tasks" / "01_task.md").write_text("---\ntitle: Task\nstatus: completed\n---\nTask body\n")

    specs.update_status("research_spec", "completed")

    completed_dir = target / ".agent_core" / "specs" / "completed" / "research_spec"
    assert not spec_dir.exists()
    assert (completed_dir / "spec.md").is_file()
    assert (completed_dir / "legal_migration_research.md").read_text() == "Research notes\n"
    assert (completed_dir / "tasks" / "01_task.md").is_file()
