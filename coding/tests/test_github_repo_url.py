import importlib.util
from dataclasses import dataclass
from types import ModuleType

import pytest
from helpers import HARNESS_ROOT

PARSE_CASES = [
    ("https://github.com/owner/repo.git", ("owner", "repo")),
    ("https://github.com/owner/repo", ("owner", "repo")),
    ("https://oauth2:token@github.com/owner/repo.git", ("owner", "repo")),
    ("git@github.com:owner/repo.git", ("owner", "repo")),
    ("git@github.com:owner/repo", ("owner", "repo")),
    (
        "git@github-tendanimukhithi:Zero-Carbon-Charge/charge_mobile_app.git",
        ("Zero-Carbon-Charge", "charge_mobile_app"),
    ),
    ("git@github.com-work:owner/repo.git", ("owner", "repo")),
    ("git@ssh.github.com:owner/repo.git", ("owner", "repo")),
    ("git@gitlab.com:owner/repo.git", ("owner", "repo")),
    ("ssh://git@github.com/owner/repo.git", ("owner", "repo")),
    ("ssh://git@github.com:22/owner/repo.git", ("owner", "repo")),
    (
        "ssh://git@github-tendanimukhithi/Zero-Carbon-Charge/charge_mobile_app.git",
        ("Zero-Carbon-Charge", "charge_mobile_app"),
    ),
    ("ssh://git@github-alias:22/owner/repo.git", ("owner", "repo")),
    ("  git@github.com:owner/repo.git  ", ("owner", "repo")),
    ("https://gitlab.com/owner/repo.git", None),
    ("https://github.company.com/owner/repo.git", None),
    ("git@github.com:", None),
    ("https://github.com/owner", None),
    ("ssh://git@github.com/owner", None),
    ("not-a-url", None),
    ("", None),
]


def _load_harness_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


def _load_setup_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("coding_setup", HARNESS_ROOT / "setup.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("url", "expected"), PARSE_CASES)
def test_parse_repo_url(monkeypatch: pytest.MonkeyPatch, url: str, expected: tuple[str, str] | None) -> None:
    github = _load_harness_module(monkeypatch, "src.utils.github")
    assert github.parse_repo_url(url) == expected


@pytest.mark.parametrize(("url", "expected"), PARSE_CASES)
def test_setup_parse_github_repo(url: str, expected: tuple[str, str] | None) -> None:
    setup = _load_setup_module()
    assert setup.parse_github_repo(url) == expected


def test_repo_name_explains_unparseable_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    github = _load_harness_module(monkeypatch, "src.utils.github")

    @dataclass(frozen=True)
    class FakeGitResult:
        stdout: str = "not-a-github-url\n"

    monkeypatch.setattr(github, "run_git", lambda *_args, **_kwargs: FakeGitResult())

    with pytest.raises(github.GitHubError, match="Could not parse origin as a GitHub repository URL") as error:
        github.repo_name()

    message = str(error.value)
    assert "not-a-github-url" in message
    assert "git@<host>:owner/repo.git" in message
    assert "ssh://git@<host>/owner/repo.git" in message
    assert "https://github.com/owner/repo.git" in message
