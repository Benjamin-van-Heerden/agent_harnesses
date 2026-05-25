import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from src.config.paths import PROJECT_PATHS


SETUP_URL = "https://raw.githubusercontent.com/Benjamin-van-Heerden/agent_harnesses/main/legal/setup.py"
SKIP_ENV_VAR = "AGENT_CORE_SKIP_AUTO_UPDATE"
DEFAULT_UPDATE_INTERVAL_DAYS = 3


class AutoUpdateError(Exception):
    pass


@dataclass(frozen=True)
class AutoUpdateResult:
    updated: bool
    reexec_required: bool = False
    skipped_reason: str | None = None


def _run_git(args: list[str], cwd: Path = PROJECT_PATHS.project_root) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _is_git_worktree() -> bool:
    inside = _run_git(["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0:
        return False
    git_dir = _run_git(["rev-parse", "--git-dir"])
    common_dir = _run_git(["rev-parse", "--git-common-dir"])
    if git_dir.returncode != 0 or common_dir.returncode != 0:
        return False
    git_path = (PROJECT_PATHS.project_root / git_dir.stdout.strip()).resolve()
    common_path = (PROJECT_PATHS.project_root / common_dir.stdout.strip()).resolve()
    return git_path != common_path


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with open(path, "rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _harness_config() -> tuple[datetime | None, int]:
    raw = _read_toml(PROJECT_PATHS.config_file)
    harness = raw.get("harness")
    if not isinstance(harness, dict):
        return None, DEFAULT_UPDATE_INTERVAL_DAYS
    last_updated_at = _parse_timestamp(harness.get("last_updated_at"))
    interval_value = harness.get("update_interval_days", DEFAULT_UPDATE_INTERVAL_DAYS)
    interval_days = interval_value if isinstance(interval_value, int) else DEFAULT_UPDATE_INTERVAL_DAYS
    if interval_days < 0:
        interval_days = DEFAULT_UPDATE_INTERVAL_DAYS
    return last_updated_at, interval_days


def _update_due_reason() -> tuple[bool, str]:
    last_updated_at, interval_days = _harness_config()
    if interval_days == 0:
        return False, "disabled by update_interval_days = 0"
    if last_updated_at is None:
        return True, "no last_updated_at is recorded"
    elapsed = datetime.now(UTC) - last_updated_at
    if elapsed >= timedelta(days=interval_days):
        return True, f"last update was at {last_updated_at.isoformat()}; interval is {interval_days} day(s)"
    return False, f"last update was at {last_updated_at.isoformat()}; interval is {interval_days} day(s)"


def _run_remote_setup_update() -> None:
    code = (
        "import urllib.request; "
        f"exec(urllib.request.urlopen({SETUP_URL!r}).read())"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code, "--", "--update"],
        cwd=PROJECT_PATHS.project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        return

    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    raise AutoUpdateError(output or "harness update failed")


def update(force: bool = False) -> AutoUpdateResult:
    if os.environ.get(SKIP_ENV_VAR):
        return AutoUpdateResult(updated=False, skipped_reason=f"{SKIP_ENV_VAR} is set")
    if _is_git_worktree():
        return AutoUpdateResult(updated=False, skipped_reason="current checkout is a worktree")
    if not force:
        due, reason = _update_due_reason()
        if not due:
            return AutoUpdateResult(updated=False, skipped_reason=f"not due; {reason}")
        print(f"Harness auto-update: update due; updating. Reason: {reason}")
    else:
        print("Harness auto-update: force update requested; updating.")

    _run_remote_setup_update()
    return AutoUpdateResult(updated=True, reexec_required=True)


def maybe_update() -> AutoUpdateResult:
    return update(force=False)


def reexec_current_command() -> None:
    os.execv(sys.executable, [sys.executable, "-B", *sys.argv])
