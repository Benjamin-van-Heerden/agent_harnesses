import io
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from types import ModuleType
from typing import Self
from urllib.error import HTTPError
from urllib.request import Request

import pytest
from helpers import HARNESS_ROOT


def _load_module(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    module = __import__(module_name, fromlist=[""])
    assert isinstance(module, ModuleType)
    return module


@dataclass(frozen=True)
class FakeProjectPaths:
    project_root: Path
    harness_root: Path


def test_auto_update_removes_python_cache_artifacts_before_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    harness_root = tmp_path / ".agent_core" / "harness"
    cache_dir = harness_root / "src" / "__pycache__"
    cache_dir.mkdir(parents=True)
    (cache_dir / "module.cpython-314.pyc").write_bytes(b"cache")
    stray_cache = harness_root / "stray.pyc"
    stray_cache.write_bytes(b"cache")
    (harness_root / "main.py").write_text("print('ok')\n")

    monkeypatch.setattr(
        auto_update,
        "PROJECT_PATHS",
        FakeProjectPaths(project_root=tmp_path, harness_root=harness_root),
    )
    monkeypatch.setenv(auto_update.SKIP_ENV_VAR, "1")

    result = auto_update.update()

    assert result.skipped_reason == f"{auto_update.SKIP_ENV_VAR} is set"
    assert not cache_dir.exists()
    assert not stray_cache.exists()
    assert (harness_root / "main.py").exists()


@dataclass(frozen=True)
class FakeBranches:
    dev: str = "dev"


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _http_error(url: str, code: int, message: str = "Backend.max_conn reached") -> HTTPError:
    return HTTPError(url, code, message, EmailMessage(), io.BytesIO(message.encode()))


def _prepare_due_auto_update(
    auto_update: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    harness_root = tmp_path / ".agent_core" / "harness"
    harness_root.mkdir(parents=True)
    monkeypatch.setattr(auto_update, "PROJECT_PATHS", FakeProjectPaths(project_root=tmp_path, harness_root=harness_root))
    monkeypatch.delenv(auto_update.SKIP_ENV_VAR, raising=False)
    monkeypatch.setattr(auto_update.worktrees, "is_worktree", lambda: False)
    monkeypatch.setattr(auto_update.git, "current_branch", lambda: "dev")
    monkeypatch.setattr(auto_update, "get_branch_names", lambda: FakeBranches())
    monkeypatch.setattr(auto_update, "_update_due_reason", lambda: (True, "due"))


def test_archive_urls_do_not_use_raw_githubusercontent(monkeypatch: pytest.MonkeyPatch) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    assert auto_update.ARCHIVE_URLS
    for url in auto_update.ARCHIVE_URLS:
        assert "raw.githubusercontent.com" not in url


def test_read_url_fails_immediately_on_http_503(monkeypatch: pytest.MonkeyPatch) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    attempts = {"count": 0}

    def urlopen(request: Request, timeout: float | None = None) -> FakeResponse:
        assert timeout == auto_update.DOWNLOAD_TIMEOUT_SECONDS
        attempts["count"] += 1
        raise _http_error(str(request.full_url), 503)

    monkeypatch.setattr(auto_update.urllib.request, "urlopen", urlopen)

    with pytest.raises(HTTPError) as error:
        auto_update._read_url("https://example.invalid/archive.zip")

    assert error.value.code == 503
    assert attempts["count"] == 1


def test_download_template_archive_falls_back_to_second_source(monkeypatch: pytest.MonkeyPatch) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    monkeypatch.setattr(
        auto_update,
        "ARCHIVE_URLS",
        (
            "https://example.invalid/first.zip",
            "https://example.invalid/second.zip",
        ),
    )
    seen: list[str] = []

    def urlopen(request: Request, timeout: float | None = None) -> FakeResponse:
        url = str(request.full_url)
        seen.append(url)
        if url.endswith("/first.zip"):
            raise _http_error(url, 503)
        return FakeResponse(b"from-second")

    monkeypatch.setattr(auto_update.urllib.request, "urlopen", urlopen)

    body = auto_update._download_template_archive()

    assert body == b"from-second"
    assert seen == ["https://example.invalid/first.zip", "https://example.invalid/second.zip"]


def test_maybe_update_continues_when_github_download_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    _prepare_due_auto_update(auto_update, monkeypatch, tmp_path)

    def fail_download() -> bytes:
        raise auto_update.TransientDownloadError("could not download the harness template archive from GitHub (HTTP 503)")

    monkeypatch.setattr(auto_update, "_download_template_archive", fail_download)

    result = auto_update.maybe_update()

    assert result.updated is False
    assert result.reexec_required is False
    assert result.skipped_reason is not None
    assert "HTTP 503" in result.skipped_reason
    assert "Continuing with the installed harness" in result.skipped_reason


def test_force_update_still_fails_when_github_download_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    _prepare_due_auto_update(auto_update, monkeypatch, tmp_path)

    def fail_download() -> bytes:
        raise auto_update.TransientDownloadError("HTTP 503")

    monkeypatch.setattr(auto_update, "_download_template_archive", fail_download)

    with pytest.raises(auto_update.AutoUpdateError, match="HTTP 503"):
        auto_update.update(force=True)


def test_find_setup_script_requires_coding_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    auto_update = _load_module(monkeypatch, "src.utils.auto_update")
    root = tmp_path / "extract"
    template = root / "agent_harnesses-main" / "coding"
    (template / ".agent_core" / "harness").mkdir(parents=True)
    (template / "setup.py").write_text("print('ok')\n")

    found = auto_update._find_setup_script(root)

    assert found == template / "setup.py"
