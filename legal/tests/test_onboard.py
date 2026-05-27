from pathlib import Path

from helpers import assert_ascii_safe, harness_command, run_command, run_setup


def test_installed_onboard_command_runs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    result = run_command([*harness_command(), "onboard"], cwd=target)

    assert result.returncode == 0
    assert "Legal onboard context" in result.stdout
    assert "Required docs" in result.stdout
    assert "# .praxis/core_docs/legal_context.typ" in result.stdout
    assert "legal_harness_function.md" not in result.stdout
    assert "You must read the relevant profile" in result.stdout
    assert_ascii_safe(result.stdout)


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
    assert "Session work log" in first.stdout
    assert "\nTodos\n-----" not in first.stdout
    assert "surfaced todos" not in first.stdout
    logs_root = target / ".praxis" / "local_context" / "logs"
    first_logs = sorted(logs_root.glob("*.md"))
    assert len(first_logs) == 1
    assert "## What was done\n_TODO_" in first_logs[0].read_text()

    second = run_command([*harness, "onboard"], cwd=target)
    assert "Removed empty work logs: 1" in second.stdout
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
    assert "Removed empty work logs" not in third.stdout
    assert len(sorted(logs_root.glob("*.md"))) == 2
