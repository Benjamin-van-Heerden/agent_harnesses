from __future__ import annotations

import sys

from helpers import PROJECT_ROOT, command_env, run_command, write_legacy_state


def test_to_harness_dry_run_summarizes_without_mutating(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    write_legacy_state(target)

    dry_run = run_command(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "migrate",
            str(target),
            "--to-harness",
            "--dry-run",
        ],
        cwd=PROJECT_ROOT,
        env=command_env(),
    )

    assert dry_run.returncode == 0
    assert not (target / ".agent_core").exists()
    assert (target / ".mem").exists()


def test_to_harness_requires_github_before_writing_state(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    write_legacy_state(target)

    result = run_command(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "migrate",
            str(target),
            "--to-harness",
        ],
        cwd=PROJECT_ROOT,
        env=command_env({"GITHUB_TOKEN": ""}),
        check=False,
    )

    assert result.returncode == 1
    assert (target / ".mem").exists()
    assert not (target / ".mem.bak").exists()
    assert not (target / ".agent_core").exists()


def test_to_harness_explains_two_step_lite_migration(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    (target / "agent_rules").mkdir()

    result = run_command(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "migrate",
            str(target),
            "--to-harness",
        ],
        cwd=PROJECT_ROOT,
        env=command_env(),
        check=False,
    )

    assert result.returncode == 1
    assert "run `migrate --lite-to-mem` first" in result.stdout
