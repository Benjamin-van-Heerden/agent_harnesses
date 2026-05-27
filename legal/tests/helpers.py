import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


LEGAL_ROOT = Path(__file__).resolve().parents[1]


def assert_ascii_safe(text: str) -> None:
    non_ascii = sorted({character for character in text if ord(character) > 127})
    assert non_ascii == []


def run_command(
    args: list[str],
    cwd: Path,
    check: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


def run_setup(target: Path, update: bool = False) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, "-B", str(LEGAL_ROOT / "setup.py")]
    if update:
        args.append("--update")
    return run_command(args, cwd=target)


def read_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as file:
        data = tomllib.load(file)
    return data if isinstance(data, dict) else {}


def harness_command() -> list[str]:
    return [sys.executable, "-B", ".praxis/harness/main.py"]
