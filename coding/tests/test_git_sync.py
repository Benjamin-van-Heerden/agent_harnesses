from pathlib import Path
from types import ModuleType

import pytest

from helpers import HARNESS_ROOT, configure_git, run_command


def _load_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


def _rev_parse(repo: Path, revision: str) -> str:
    result = run_command(["git", "rev-parse", revision], cwd=repo)
    return result.stdout.strip()


def test_protected_branch_sync_does_not_mutate_non_current_protected_branches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remote = tmp_path / "remote.git"
    run_command(["git", "init", "--bare", remote.as_posix()], cwd=tmp_path)

    project = tmp_path / "project"
    project.mkdir()
    run_command(["git", "init", "-b", "dev"], cwd=project)
    configure_git(project)
    (project / ".agent_core").mkdir()
    (project / ".agent_core" / "dev.txt").write_text("dev\n")
    run_command(["git", "add", ".agent_core/dev.txt"], cwd=project)
    run_command(["git", "commit", "-m", "initial dev"], cwd=project)
    run_command(["git", "branch", "test"], cwd=project)
    run_command(["git", "branch", "main"], cwd=project)
    run_command(["git", "remote", "add", "origin", remote.as_posix()], cwd=project)
    run_command(["git", "push", "origin", "dev", "test", "main"], cwd=project)

    updater = tmp_path / "updater"
    run_command(["git", "clone", remote.as_posix(), updater.as_posix()], cwd=tmp_path)
    configure_git(updater)
    run_command(["git", "checkout", "main"], cwd=updater)
    (updater / ".agent_core" / "main.txt").write_text("main\n")
    run_command(["git", "add", ".agent_core/main.txt"], cwd=updater)
    run_command(["git", "commit", "-m", "advance main"], cwd=updater)
    run_command(["git", "push", "origin", "main"], cwd=updater)
    run_command(["git", "checkout", "test"], cwd=updater)
    (updater / ".agent_core" / "test.txt").write_text("test\n")
    run_command(["git", "add", ".agent_core/test.txt"], cwd=updater)
    run_command(["git", "commit", "-m", "advance test"], cwd=updater)
    run_command(["git", "push", "origin", "test"], cwd=updater)

    git_module = _load_module(monkeypatch, "src.utils.git")
    config_models = _load_module(monkeypatch, "src.config.models")
    branches = config_models.BranchNames(dev="dev", test="test", main="main")

    git_module.protected_branch_sync(branches, cwd=project)

    current_branch = run_command(["git", "branch", "--show-current"], cwd=project)
    assert current_branch.stdout.strip() == "dev"
    assert not (project / ".agent_core" / "main.txt").exists()
    assert not (project / ".agent_core" / "test.txt").exists()
    assert _rev_parse(project, "main") != _rev_parse(project, "origin/main")
    assert _rev_parse(project, "test") != _rev_parse(project, "origin/test")
