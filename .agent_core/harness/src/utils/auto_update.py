import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from src.config.branches import get_branch_names
from src.config.main import read_toml
from src.config.paths import PROJECT_PATHS
from src.utils import git, worktrees
from src.utils.errors import GitError

ARCHIVE_URLS = (
    "https://github.com/Benjamin-van-Heerden/agent_harnesses/archive/refs/heads/main.zip",
    "https://codeload.github.com/Benjamin-van-Heerden/agent_harnesses/zip/refs/heads/main",
)
SKIP_ENV_VAR = "AGENT_CORE_SKIP_AUTO_UPDATE"
DEFAULT_UPDATE_INTERVAL_DAYS = 1
DOWNLOAD_TIMEOUT_SECONDS = 8
DOWNLOAD_FAILED_EXIT_CODE = 2
DOWNLOAD_USER_AGENT = "AgentCoreHarness"


class AutoUpdateError(Exception):
    pass


class TransientDownloadError(AutoUpdateError):
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


def _update_due() -> bool:
    due, _reason = _update_due_reason()
    return due


def _remove_python_cache_artifacts(root: Path) -> None:
    if not root.exists():
        return

    for cache_dir in sorted(
        (path for path in root.rglob("__pycache__") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        shutil.rmtree(cache_dir)
        print(f"Removed Python cache directory: {cache_dir.relative_to(PROJECT_PATHS.project_root)}")

    for cache_file in sorted(path for path in root.rglob("*.pyc") if path.is_file()):
        cache_file.unlink()
        print(f"Removed Python cache file: {cache_file.relative_to(PROJECT_PATHS.project_root)}")


def _describe_download_error(url: str, error: Exception) -> str:
    if isinstance(error, urllib.error.HTTPError):
        return f"{url} -> HTTP {error.code}"
    return f"{url} -> {error}"


def _read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": DOWNLOAD_USER_AGENT})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
        return response.read()


def _download_template_archive() -> bytes:
    errors: list[str] = []
    for url in ARCHIVE_URLS:
        try:
            return _read_url(url)
        except (urllib.error.URLError, TimeoutError) as error:
            errors.append(_describe_download_error(url, error))
    detail = "; ".join(errors) if errors else "no download sources"
    raise TransientDownloadError(f"could not download the harness template archive from GitHub ({detail})")


def _find_setup_script(extract_root: Path) -> Path:
    for candidate in sorted(extract_root.iterdir()):
        setup_path = candidate / "coding" / "setup.py"
        harness_root = candidate / "coding" / ".agent_core" / "harness"
        if setup_path.is_file() and harness_root.is_dir():
            return setup_path
    raise TransientDownloadError("downloaded archive did not contain coding/setup.py")


def _run_remote_setup_update() -> None:
    archive = _download_template_archive()
    with tempfile.TemporaryDirectory(prefix="agent-core-update-") as temp_name:
        extract_root = Path(temp_name)
        with zipfile.ZipFile(io.BytesIO(archive)) as repo_zip:
            repo_zip.extractall(extract_root)
        setup_path = _find_setup_script(extract_root)
        result = subprocess.run(
            [sys.executable, "-B", str(setup_path), "--update"],
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
    if result.returncode == DOWNLOAD_FAILED_EXIT_CODE:
        raise TransientDownloadError(output or "could not download harness templates from GitHub")
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


def update(force: bool = False, *, continue_on_download_failure: bool = False) -> AutoUpdateResult:
    _remove_python_cache_artifacts(PROJECT_PATHS.harness_root)

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
    if not force:
        due, reason = _update_due_reason()
        if not due:
            return AutoUpdateResult(updated=False, skipped_reason=f"not due; {reason}")
        print(f"Harness auto-update: update due; updating. Reason: {reason}")
    else:
        print("Harness auto-update: force update requested; updating.")

    try:
        _run_remote_setup_update()
    except TransientDownloadError as error:
        if not continue_on_download_failure:
            raise AutoUpdateError(str(error)) from error
        return AutoUpdateResult(
            updated=False,
            skipped_reason=(
                f"{error}. Continuing with the installed harness. "
                "The next onboard will retry because last_updated_at was not changed."
            ),
        )
    _commit_update_changes()
    return AutoUpdateResult(updated=True, reexec_required=True)


def maybe_update() -> AutoUpdateResult:
    return update(force=False, continue_on_download_failure=True)


def reexec_current_command() -> None:
    os.execv(sys.executable, [sys.executable, "-B", *sys.argv])
