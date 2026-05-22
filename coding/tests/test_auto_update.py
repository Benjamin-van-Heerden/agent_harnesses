from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

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
