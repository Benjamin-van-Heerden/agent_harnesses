import subprocess
from pathlib import Path
from types import ModuleType

import pytest
from helpers import HARNESS_ROOT, configure_git


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_commit(repo: Path, path: str, content: str, message: str) -> str:
    file_path = repo / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    _run_git(["add", path], repo)
    _run_git(["commit", "-m", message], repo)
    return _run_git(["rev-parse", "HEAD"], repo)


def _build_divergent_promotion_repo(tmp_path: Path) -> Path:
    """Reproduce GitHub merge-commit pollution on main while dev/test moved forward.

    Shape matches the real incident: main's only unique tip is a merge commit whose second
    parent already sits on the linear line, then newer linear commits land on dev/test.
    """
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "clone", str(remote), str(work)], check=True, capture_output=True, text=True)
    configure_git(work)

    _run_git(["checkout", "-b", "dev"], work)
    _write_commit(work, "base.txt", "base\n", "base")
    shared = _run_git(["rev-parse", "HEAD"], work)
    _run_git(["branch", "main", shared], work)
    _write_commit(work, "promoted.txt", "promoted\n", "settlement work already on linear line")
    snapshot = _run_git(["rev-parse", "HEAD"], work)
    _run_git(["branch", "test", snapshot], work)

    # GitHub-style merge of a promotion snapshot into main (second parent already on the line).
    _run_git(["checkout", "main"], work)
    _run_git(
        [
            "merge",
            "--no-ff",
            "-m",
            "Merge pull request #21 from promotion/main/example",
            snapshot,
        ],
        work,
    )

    # Newer work continues on the linear line after the polluted main tip.
    _run_git(["checkout", "dev"], work)
    _write_commit(work, "linear.txt", "linear-1\n", "linear commit one")
    _write_commit(work, "linear.txt", "linear-2\n", "linear commit two")
    linear_tip = _run_git(["rev-parse", "HEAD"], work)
    _run_git(["branch", "-f", "test", linear_tip], work)
    _run_git(["push", "-u", "origin", "dev", "test", "main"], work)
    return work


def _load_modules(monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, ModuleType, type[BaseException]]:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    reunify = __import__("src.utils.promotion_reunify", fromlist=[""])
    git = __import__("src.utils.git", fromlist=[""])
    errors = __import__("src.utils.errors", fromlist=[""])
    assert isinstance(reunify, ModuleType)
    assert isinstance(git, ModuleType)
    git_error = errors.GitError
    assert isinstance(git_error, type)
    return reunify, git, git_error


def test_inspect_divergence_detects_github_merge_tip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = _build_divergent_promotion_repo(tmp_path)
    monkeypatch.chdir(work)
    reunify, git, _git_error = _load_modules(monkeypatch)

    report = reunify.inspect_divergence("origin/dev", "origin/main")

    assert report.destination_tip_is_merge
    assert report.destination_only_are_merges
    assert any("Merge pull request #21" in line for line in report.destination_only)
    assert report.source_only
    assert not git.is_ancestor("origin/main", "origin/dev")


def test_reunify_merge_makes_destination_an_ancestor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = _build_divergent_promotion_repo(tmp_path)
    monkeypatch.chdir(work)
    reunify, git, _git_error = _load_modules(monkeypatch)

    result = reunify.ensure_destination_is_ancestor(
        "origin/dev",
        "origin/main",
        reunify_branch="dev",
        start_point="origin/dev",
    )

    assert result is not None
    assert result.performed
    assert git.is_ancestor("origin/main", "origin/dev")
    assert git.is_ancestor("origin/main", "dev")
    assert "Reunified promotion history" in result.message


def test_reunify_refuses_unique_non_merge_destination_commits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = _build_divergent_promotion_repo(tmp_path)
    monkeypatch.chdir(work)
    reunify, git, git_error = _load_modules(monkeypatch)
    _run_git(["checkout", "main"], work)
    _write_commit(work, "unique-main.txt", "unique\n", "unique non-merge main commit")
    _run_git(["push", "origin", "main"], work)
    _run_git(["checkout", "dev"], work)

    with pytest.raises(git_error) as error:
        reunify.ensure_destination_is_ancestor(
            "origin/dev",
            "origin/main",
            reunify_branch="dev",
            start_point="origin/dev",
        )

    message = str(error.value)
    assert "Destination-only commits include non-merge" in message
    assert not git.is_ancestor("origin/main", "origin/dev")


def test_after_reunify_dev_can_fast_forward_test_and_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = _build_divergent_promotion_repo(tmp_path)
    monkeypatch.chdir(work)
    reunify, git, _git_error = _load_modules(monkeypatch)

    reunify.ensure_destination_is_ancestor(
        "origin/dev",
        "origin/main",
        reunify_branch="dev",
        start_point="origin/dev",
    )
    git.push_ref("origin/dev", "test")
    git.fetch()
    git.push_ref("origin/test", "main")
    git.fetch()

    dev_tip = git.rev_parse("origin/dev")
    assert git.rev_parse("origin/test") == dev_tip
    assert git.rev_parse("origin/main") == dev_tip
