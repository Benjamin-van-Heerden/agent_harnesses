from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest
import typer
from github.PullRequest import PullRequest
from github.Repository import Repository
from helpers import HARNESS_ROOT


@dataclass(frozen=True)
class _Branch:
    ref: str


@dataclass(frozen=True)
class _User:
    login: str


@dataclass(frozen=True)
class _Review:
    user: _User
    state: str


@dataclass(frozen=True)
class _MergeResult:
    merged: bool


class _Pull:
    def __init__(
        self,
        number: int,
        title: str,
        head: str,
        base: str,
        *,
        merged: bool = False,
    ) -> None:
        self.number = number
        self.title = title
        self.head = _Branch(head)
        self.base = _Branch(base)
        self.user = _User("reviewer")
        self.html_url = f"https://github.example/pull/{number}"
        self.body = "Promotion description"
        self.draft = False
        self.mergeable = True
        self.mergeable_state = "clean"
        self.state = "open"
        self.merged = merged

    def update(self) -> bool:
        self.merged = True
        return True

    def get_commits(self) -> list[object]:
        return []

    def get_reviews(self) -> list[object]:
        return [_Review(_User("approver"), "APPROVED")]

    def get_issue_comments(self) -> list[object]:
        return []

    def get_review_comments(self) -> list[object]:
        return []

    def get_files(self) -> list[object]:
        return []


class _Repo:
    def __init__(self, pulls: list[_Pull] | None = None) -> None:
        self.pulls = pulls or []

    def get_pulls(
        self,
        state: str = "open",
        base: str | None = None,
        head: str | None = None,
    ) -> list[_Pull]:
        del state, head
        return [pull for pull in self.pulls if base is None or pull.base.ref == base]


class _Ref:
    def __init__(self, branch: str) -> None:
        self.ref = f"refs/heads/{branch}"
        self.deleted = False

    def delete(self) -> None:
        self.deleted = True


class _CleanupRepo:
    def __init__(self) -> None:
        self.owner = _User("reviewer")
        self.open_ref = _Ref("promotion/test/open")
        self.closed_ref = _Ref("promotion/main/closed")
        self.orphan_ref = _Ref("promotion/test/orphan")

    def get_git_matching_refs(self, _prefix: str) -> list[_Ref]:
        return [self.open_ref, self.closed_ref, self.orphan_ref]

    def get_pulls(
        self,
        state: str,
        head: str,
    ) -> list[_Pull]:
        if head.endswith("promotion/test/open") and state == "open":
            return [_Pull(1, "Open", "promotion/test/open", "test")]
        if head.endswith("promotion/main/closed") and state == "closed":
            return [_Pull(2, "Closed", "promotion/main/closed", "main")]
        return []


def _load_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


def _branches(monkeypatch: pytest.MonkeyPatch) -> object:
    models = _load_module(monkeypatch, "src.config.models")
    return models.BranchNames(dev="dev", test="test", main="main")


def test_promotion_prepare_creates_description_and_execution_instruction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)
    monkeypatch.setattr(create.git, "fetch", lambda: None)
    monkeypatch.setattr(create.git, "pull_ff_only", lambda _branch: None)
    monkeypatch.setattr(create.git, "same_commit", lambda _first, _second: True)
    monkeypatch.setattr(create, "repository", lambda: cast(Repository, _Repo()))

    create.run("test", execute=False)

    description = tmp_path / ".agent_core" / "tmp" / "promotion_test.md"
    output = capsys.readouterr().out
    assert description.is_file()
    assert "## Reviewer guide" in description.read_text()
    assert "promotion create test --execute" in output
    assert "Nothing has been pushed" in output
    assert "replacing every {PROMOTION_DESCRIPTION: ...} placeholder" in output


def test_production_promotion_checks_out_test_for_inspection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    checked_out: list[str] = []
    pulled: list[str] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)
    monkeypatch.setattr(create.git, "fetch", lambda: None)
    monkeypatch.setattr(create.git, "checkout", lambda branch: checked_out.append(branch))
    monkeypatch.setattr(create.git, "pull_ff_only", lambda branch: pulled.append(branch))
    monkeypatch.setattr(create.git, "same_commit", lambda _first, _second: True)
    monkeypatch.setattr(create, "repository", lambda: cast(Repository, _Repo()))

    create.run("main")

    output = capsys.readouterr().out
    assert checked_out == ["test"]
    assert pulled == ["test"]
    assert "You have been switched to 'test'" in output
    assert "You are preparing the promotion: test → main" in output


def test_promotion_preparation_fails_before_switching_when_github_authentication_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    checked_out: list[str] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)
    monkeypatch.setattr(create.git, "checkout", lambda branch: checked_out.append(branch))
    monkeypatch.setattr(
        create,
        "repository",
        lambda: (_ for _ in ()).throw(create.GitHubError("GitHub authentication failed: bad credentials")),
    )

    with pytest.raises(typer.Exit) as error:
        create.run("main")

    output = capsys.readouterr().err
    assert error.value.exit_code == 1
    assert checked_out == []
    assert not (tmp_path / ".agent_core" / "tmp" / "promotion_main.md").exists()
    assert "Promotion preparation requires working GitHub authentication." in output
    assert "Nothing was changed." in output


def test_promotion_execute_creates_remote_only_branch_and_pr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    monkeypatch.chdir(tmp_path)
    description = tmp_path / ".agent_core" / "tmp" / "promotion_test.md"
    description.parent.mkdir(parents=True)
    description.write_text(
        create.DESCRIPTION_PLACEHOLDER_PATTERN.sub(
            "Complete promotion description.",
            create._description_template("dev", "test"),
        )
    )
    repo = _Repo()
    pull = _Pull(42, "[Promote]: dev → test", "promotion/test/example", "test")
    pushed: list[tuple[str, str]] = []

    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)
    monkeypatch.setattr(create.git, "fetch", lambda: None)
    monkeypatch.setattr(create.git, "is_ancestor", lambda _ancestor, _descendant: True)
    monkeypatch.setattr(create.git, "same_commit", lambda _first, _second: False)
    monkeypatch.setattr(create.git, "push_ref", lambda source, branch: pushed.append((source, branch)))
    monkeypatch.setattr(create.git, "checkout", lambda _branch: None)
    monkeypatch.setattr(create, "repository", lambda: cast(Repository, repo))
    monkeypatch.setattr(
        create,
        "create_pull_request",
        lambda _repo, _title, _body, head, _base: _set_pull_head(pull, head),
    )

    create.run("test", execute=True)

    assert pushed[0][0] == "dev"
    assert pushed[0][1].startswith("promotion/test/")
    assert not description.exists()
    output = capsys.readouterr().out
    assert "The destination branch 'test' will not be advanced by this command." in output
    assert "You have been switched back to 'dev' mission control." in output


def _set_pull_head(pull: _Pull, head: str) -> PullRequest:
    pull.head = _Branch(head)
    return cast(PullRequest, pull)


def test_direct_promotion_first_requires_explicit_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)

    with pytest.raises(typer.Exit) as error:
        create.run("test", no_pr=True)

    output = capsys.readouterr().err
    assert error.value.exit_code == 1
    assert "bypasses the promotion description" in output
    assert "Are you sure you want to promote dev directly into test without a pull request?" in output
    assert "promotion create test --no-pr --force" in output


def test_confirmed_direct_promotion_fast_forwards_without_pr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    pushed: list[tuple[str, str]] = []
    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)
    monkeypatch.setattr(create.git, "fetch", lambda: None)
    monkeypatch.setattr(create.git, "is_ancestor", lambda _ancestor, _descendant: True)
    monkeypatch.setattr(
        create.git,
        "same_commit",
        lambda first, second: first in {"dev", "test", "main"} and second == f"origin/{first}",
    )
    monkeypatch.setattr(create.git, "push_ref", lambda source, branch: pushed.append((source, branch)))
    monkeypatch.setattr(create.git, "update_local_branch", lambda _branch, _revision: None)
    monkeypatch.setattr(create, "repository", lambda: cast(Repository, _Repo()))

    create.run("test", no_pr=True, force=True)

    assert pushed == [("origin/dev", "test")]
    output = capsys.readouterr().out
    assert "Local 'test' now matches 'origin/test'." in output
    assert "No promotion description, snapshot branch, or pull request was created." in output


def test_direct_promotion_refuses_mismatched_local_protected_branch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    create = _load_module(monkeypatch, "src.commands.promotion.create")
    pushed: list[tuple[str, str]] = []
    monkeypatch.setattr(create, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(create.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(create.git, "has_uncommitted_changes", lambda: False)
    monkeypatch.setattr(create.git, "fetch", lambda: None)
    monkeypatch.setattr(
        create.git,
        "same_commit",
        lambda first, second: first != "test" and second == f"origin/{first}",
    )
    monkeypatch.setattr(create.git, "push_ref", lambda source, branch: pushed.append((source, branch)))

    with pytest.raises(typer.Exit) as error:
        create.run("test", no_pr=True, force=True)

    assert error.value.exit_code == 1
    assert pushed == []
    assert "'test' and 'origin/test'" in capsys.readouterr().err


def test_pr_discovery_requires_user_to_choose(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review = _load_module(monkeypatch, "src.commands.pr.review")
    repo = _Repo(
        [
            _Pull(42, "[Promote]: test → main", "promotion/main/example", "main"),
            _Pull(43, "[Complete]: Feature", "dev-user-feature", "dev"),
        ]
    )
    monkeypatch.setattr(review, "repository", lambda: cast(Repository, repo))
    monkeypatch.setattr(review, "get_branch_names", lambda: _branches(monkeypatch))

    review.run()

    output = capsys.readouterr().out
    assert "#42 [promotion]" in output
    assert "#43 [pull request]" in output
    assert "You must ask the user which pull request they mean." in output
    assert "production confirmation required" in output


def test_pr_review_context_uses_pr_body_as_promotion_description(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _load_module(monkeypatch, "src.commands.pr.review")
    pull = cast(
        PullRequest,
        _Pull(42, "[Promote]: test → main", "promotion/main/example", "main"),
    )

    context = review._review_context(pull)

    assert "## Pull request description" in context
    assert "Promotion description" in context
    assert "treat the pull request body as a guide, not as proof" in context


def test_main_pr_merge_without_force_requires_explicit_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    merge = _load_module(monkeypatch, "src.commands.pr.merge")
    pull = cast(
        PullRequest,
        _Pull(42, "[Promote]: test → main", "promotion/main/example", "main"),
    )
    monkeypatch.setattr(merge, "get_branch_names", lambda: _branches(monkeypatch))

    with pytest.raises(typer.Exit) as error:
        merge._require_production_confirmation(pull, force=False)

    output = capsys.readouterr().err
    assert error.value.exit_code == 1
    assert "Are you sure you want to promote PR #42 into production?" in output
    assert "pr merge 42 --force" in output


def test_promotion_merge_fast_forwards_and_deletes_remote_branch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    merge = _load_module(monkeypatch, "src.commands.pr.merge")
    pull = _Pull(42, "[Promote]: dev → test", "promotion/test/example", "test")
    pushed: list[tuple[str, str]] = []
    deleted: list[str] = []
    monkeypatch.setattr(merge, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(merge.git, "fetch", lambda: None)
    monkeypatch.setattr(merge.git, "is_ancestor", lambda _ancestor, _descendant: True)
    monkeypatch.setattr(merge.git, "push_ref", lambda source, target: pushed.append((source, target)))
    monkeypatch.setattr(
        merge,
        "delete_remote_branch",
        lambda _repo, branch: deleted.append(branch) is None,
    )

    merge._merge_promotion(
        cast(Repository, _Repo([pull])),
        cast(PullRequest, pull),
    )

    assert pushed == [("origin/promotion/test/example", "test")]
    assert deleted == ["promotion/test/example"]
    assert "with a fast-forward" in capsys.readouterr().out


def test_normal_pr_merge_uses_single_resolved_pull_request(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    merge = _load_module(monkeypatch, "src.commands.pr.merge")
    pull = _Pull(43, "[Complete]: Feature", "dev-reviewer-feature", "dev")
    checked_out: list[str] = []
    merged: list[_Pull] = []
    monkeypatch.setattr(merge, "get_branch_names", lambda: _branches(monkeypatch))
    monkeypatch.setattr(merge.specs, "list_all", list)
    monkeypatch.setattr(
        merge,
        "squash_pull_request",
        lambda selected, _message: merged.append(selected) or _MergeResult(merged=True),
    )
    monkeypatch.setattr(merge.git, "fetch", lambda: None)
    monkeypatch.setattr(merge.git, "checkout", lambda branch: checked_out.append(branch))
    monkeypatch.setattr(merge.git, "pull_ff_only", lambda _branch: None)
    monkeypatch.setattr(merge.git, "current_branch", lambda: "dev")

    merge._merge_normal_pull_request(
        cast(Repository, _Repo([pull])),
        cast(PullRequest, pull),
        None,
    )

    assert merged == [pull]
    assert checked_out == ["dev"]
    assert "Merged pull request #43 into 'dev'." in capsys.readouterr().out


def test_sync_cleanup_deletes_only_closed_promotion_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync = _load_module(monkeypatch, "src.commands.sync.main")
    repo = _CleanupRepo()

    cleaned = sync._cleanup_closed_promotion_branches(cast(Repository, repo))

    assert cleaned == 1
    assert not repo.open_ref.deleted
    assert repo.closed_ref.deleted
    assert not repo.orphan_ref.deleted
