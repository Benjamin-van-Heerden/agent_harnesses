import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import cast

from src.config.branches import get_branch_names
from src.config.main import read_toml
from src.config.paths import PROJECT_PATHS
from src.utils import git, worktrees
from src.utils.errors import GitError


SETUP_URL = "https://raw.githubusercontent.com/Benjamin-van-Heerden/agent_harnesses/main/coding/setup.py"
SKIP_ENV_VAR = "AGENT_CORE_SKIP_AUTO_UPDATE"
DEFAULT_UPDATE_INTERVAL_DAYS = 3


class AutoUpdateError(Exception):
    pass


@dataclass(frozen=True)
class AutoUpdateResult:
    updated: bool
    reexec_required: bool = False
    skipped_reason: str | None = None


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


def _harness_config() -> tuple[datetime | None, int]:
    raw = read_toml(PROJECT_PATHS.config_file)
    harness_value = raw.get("harness")
    if not isinstance(harness_value, dict):
        return None, DEFAULT_UPDATE_INTERVAL_DAYS
    harness = cast(dict[str, object], harness_value)

    last_updated_at = _parse_timestamp(harness.get("last_updated_at"))
    interval_value = harness.get("update_interval_days", DEFAULT_UPDATE_INTERVAL_DAYS)
    interval_days = interval_value if isinstance(interval_value, int) else DEFAULT_UPDATE_INTERVAL_DAYS
    if interval_days < 0:
        interval_days = DEFAULT_UPDATE_INTERVAL_DAYS
    return last_updated_at, interval_days


def _update_due() -> bool:
    last_updated_at, interval_days = _harness_config()
    if interval_days == 0:
        return False
    if last_updated_at is None:
        return True
    return datetime.now(UTC) - last_updated_at >= timedelta(days=interval_days)


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


def _commit_update_changes() -> None:
    if not git.has_uncommitted_changes():
        return

    branch = git.current_branch()
    message = f"harness updated {datetime.now(UTC).strftime('%Y%m%d')}"
    try:
        git.add_all()
        if git.commit(message):
            git.push(branch)
    except GitError as error:
        raise AutoUpdateError(f"could not commit and push harness update: {error}") from error


def update(force: bool = False) -> AutoUpdateResult:
    if os.environ.get(SKIP_ENV_VAR):
        return AutoUpdateResult(updated=False, skipped_reason=f"{SKIP_ENV_VAR} is set")
    if worktrees.is_worktree():
        return AutoUpdateResult(updated=False, skipped_reason="current checkout is a worktree")

    branches = get_branch_names()
    current = git.current_branch()
    if current != branches.dev:
        return AutoUpdateResult(
            updated=False,
            skipped_reason=f"current branch is not configured dev branch '{branches.dev}'",
        )
    if not force and not _update_due():
        return AutoUpdateResult(updated=False)

    _run_remote_setup_update()
    _commit_update_changes()
    return AutoUpdateResult(updated=True, reexec_required=True)


def maybe_update() -> AutoUpdateResult:
    return update(force=False)


def reexec_current_command() -> None:
    os.execv(sys.executable, [sys.executable, "-B", *sys.argv])
