import importlib.util
import io
from email.message import EmailMessage
from types import ModuleType
from typing import Self
from urllib.error import HTTPError
from urllib.request import Request

import pytest
from helpers import HARNESS_ROOT


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def _load_setup_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("coding_setup_download", HARNESS_ROOT / "setup.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _http_error(url: str, code: int, message: str = "Backend.max_conn reached") -> HTTPError:
    return HTTPError(url, code, message, EmailMessage(), io.BytesIO(message.encode()))


def test_setup_download_bytes_fails_immediately_on_http_503(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = _load_setup_module()
    attempts = {"count": 0}

    def urlopen(request: Request, timeout: float | None = None) -> FakeResponse:
        assert timeout == setup.DOWNLOAD_TIMEOUT_SECONDS
        attempts["count"] += 1
        raise _http_error(str(request.full_url), 503)

    monkeypatch.setattr(setup.urllib.request, "urlopen", urlopen)

    with pytest.raises(setup.DownloadError, match="HTTP 503"):
        setup.download_bytes("https://example.invalid/archive.zip")

    assert attempts["count"] == 1


def test_setup_download_template_archive_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    setup = _load_setup_module()
    monkeypatch.setattr(setup, "REPO_ARCHIVE_URL", "https://example.invalid/first.zip")
    monkeypatch.setattr(setup, "REPO_ARCHIVE_FALLBACK_URL", "https://example.invalid/second.zip")
    seen: list[str] = []

    def urlopen(request: Request, timeout: float | None = None) -> FakeResponse:
        url = str(request.full_url)
        seen.append(url)
        if url.endswith("/first.zip"):
            raise _http_error(url, 503)
        return FakeResponse(b"archive-bytes")

    monkeypatch.setattr(setup.urllib.request, "urlopen", urlopen)

    body = setup.download_template_archive()

    assert body == b"archive-bytes"
    assert seen == ["https://example.invalid/first.zip", "https://example.invalid/second.zip"]
