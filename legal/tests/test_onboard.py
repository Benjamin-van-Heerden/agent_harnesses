import sys
from pathlib import Path

from helpers import (
    assert_ascii_safe,
    harness_command,
    onboard_content,
    run_command,
    run_setup,
)


def test_installed_onboard_command_runs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    result = run_command([*harness_command(), "onboard"], cwd=target)
    content = onboard_content(result, target)

    assert result.returncode == 0
    assert "Legal onboard context written to: .praxis/tmp/onboard_" in result.stdout
    assert "NB: YOU MUST read it in full before proceeding" in result.stdout
    assert "Legal onboard context" in content
    assert "Required docs" in content
    assert "# .praxis/core_docs/legal_context.typ" in content
    assert "Critical legal context warning" in content
    assert "legal context file has not been set up" in content
    assert "strongly warn the lawyer" in content
    assert "legal_harness_function.md" not in content
    assert "You must read the relevant profile" in content
    assert "current session work log" in content
    assert_ascii_safe(result.stdout)
    assert_ascii_safe(content)


def test_onboard_omits_legal_context_warning_once_context_is_filled(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)
    (target / ".praxis" / "core_docs" / "legal_context.typ").write_text(
        "= Legal Context\n\nThis practice handles ordinary civil litigation.\n"
    )

    result = run_command([*harness_command(), "onboard"], cwd=target)
    content = onboard_content(result, target)

    assert "Critical legal context warning" not in content
    assert "strongly warn the lawyer" not in content


def test_onboard_snapshots_state_but_regular_commands_do_not_snapshot_on_exit(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)
    run_command(["git", "config", "user.email", "agent@example.test"], cwd=target)
    run_command(["git", "config", "user.name", "Agent"], cwd=target)

    harness = harness_command()
    onboard = run_command([*harness, "onboard"], cwd=target)
    assert "Created local git snapshot:" in onboard.stdout
    assert (target / ".praxis" / "client_matter_index.toml").is_file()
    assert (target / ".praxis" / "tmp").is_dir()
    first_commit = run_command(["git", "rev-parse", "HEAD"], cwd=target).stdout.strip()

    run_command(
        [*harness, "client", "new", "Smith Corp", "entity", "--slug", "smith"],
        cwd=target,
    )
    second_commit = run_command(["git", "rev-parse", "HEAD"], cwd=target).stdout.strip()
    assert second_commit == first_commit
    assert (
        "ZZ_CLIENTS/"
        in run_command(["git", "status", "--porcelain"], cwd=target).stdout
    )


def test_onboard_creates_session_log_and_removes_untouched_empty_logs(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()
    first = run_command([*harness, "onboard"], cwd=target)
    first_content = onboard_content(first, target)
    assert "Session work log" in first_content
    assert "You must read the current session work log now" in first_content
    assert "\nTodos\n-----" not in first_content
    assert "surfaced todos" not in first_content
    logs_root = target / ".praxis" / "local_context" / "logs"
    first_logs = sorted(logs_root.glob("*.md"))
    assert len(first_logs) == 1
    assert "## What was done\n_TODO_" in first_logs[0].read_text()

    second = run_command([*harness, "onboard"], cwd=target)
    second_content = onboard_content(second, target)
    assert "Removed empty work logs: 1" in second_content
    second_logs = sorted(logs_root.glob("*.md"))
    assert len(second_logs) == 1

    edited = second_logs[0]
    edited.write_text(
        edited.read_text().replace(
            "## What was done\n_TODO_",
            "## What was done\nOpened the file and reviewed context.",
        )
    )
    third = run_command([*harness, "onboard"], cwd=target)
    third_content = onboard_content(third, target)
    assert "Removed empty work logs" not in third_content
    assert "Recent global work logs" in third_content
    assert "Opened the file and reviewed context." in third_content
    assert len(sorted(logs_root.glob("*.md"))) == 2


def test_log_new_rejects_matter_specific_work_logs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from src.state.clients import create_client
from src.state.matters import create_matter

create_client("smith", "Smith Corp", "entity")
create_matter("smith", "litigation", "shareholder_dispute", "normal", "hourly")
""".strip()
    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )

    result = run_command(
        [*harness_command(), "log", "new", "shareholder_dispute"],
        cwd=target,
        check=False,
    )
    assert result.returncode == 1
    assert "matter-specific work logs are retired" in result.stderr
