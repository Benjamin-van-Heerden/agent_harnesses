import os
from pathlib import Path

from constants import GIT_USER_NAME
from helpers import command_env, harness_command, init_git_project, install_harness, run_command


def test_template_onboard_reads_docs_without_indexing(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    install_harness(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.write_text(
        config_path.read_text().replace(
            'symlink_paths = [".claude"]',
            'symlink_paths = [".claude", ".env"]',
        )
    )

    docs_dir = target / ".agent_core" / "docs"
    (docs_dir / "nested").mkdir()
    (docs_dir / "alpha.md").write_text("Alpha doc body\n")
    (docs_dir / "nested" / "beta.md").write_text("Beta doc body\n")

    result = run_command(
        harness_command() + ["onboard", "--stdout", "--no-sync"],
        cwd=target,
        env=command_env(),
    )

    assert "Alpha doc body" in result.stdout
    assert "Beta doc body" in result.stdout
    assert "Onboard .agent_core mutation audit: no changes detected." in result.stdout
    gitignore_lines = (target / ".gitignore").read_text().splitlines()
    assert ".env" in gitignore_lines
    assert ".env/" in gitignore_lines
    assert not (target / ".agent_core" / "tmp").exists()
    assert not (target / ".agent_core" / "docs" / "data").exists()


def test_template_onboard_expands_current_user_and_recent_logs(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    install_harness(target)

    (target / ".agent_core" / "user_mappings.toml").write_text(
        f'[octo]\nname = "{GIT_USER_NAME}"\nemail = "octo@example.com"\n'
    )

    logs_dir = target / ".agent_core" / "logs"
    for index in range(1, 5):
        (logs_dir / f"octo_2026051{index}_120000_session.md").write_text(
            f"---\ncreated_at: 2026-05-1{index}T12:00:00\nusername: octo\n---\n"
            f"Current user log {index}\n"
        )
    for index in range(1, 7):
        (logs_dir / f"other_2026041{index}_120000_session.md").write_text(
            f"---\ncreated_at: 2026-04-1{index}T12:00:00\nusername: other\n---\n"
            f"General log {index}\n"
        )

    result = run_command(
        harness_command() + ["onboard", "--stdout", "--no-sync"],
        cwd=target,
        env=command_env(),
    )

    assert "Current user log 4" in result.stdout
    assert "Current user log 3" in result.stdout
    assert "Current user log 2" in result.stdout
    assert "Current user log 1" not in result.stdout
    assert "General log 6" in result.stdout
    assert "General log 2" in result.stdout
    assert "General log 1" not in result.stdout


def test_template_onboard_warns_and_continues_when_sync_fails(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "track readme"], cwd=target)
    install_harness(target)

    (target / "README.md").write_text("# Project\nDirty tracked change\n")

    result = run_command(
        harness_command() + ["onboard", "--stdout"],
        cwd=target,
        env=command_env(),
    )

    assert "🚨 ONBOARD SYNC WARNING" in result.stdout
    assert "Working tree has uncommitted tracked changes." in result.stdout
    assert "Read this onboard output in full before proceeding." in result.stdout
    assert "Report the onboard sync warning and its reason." in result.stdout
    assert "Project" in result.stdout


def test_template_onboard_reports_agent_core_tmp_mutations(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    install_harness(target)

    docs_dir = target / ".agent_core" / "docs"
    (docs_dir / "large.md").write_text("Large doc body\n" + ("x" * 15000))

    temp_dir = target / ".agent_core" / "tmp"
    temp_dir.mkdir()
    stale_output = temp_dir / "onboard_20000101_000000.md"
    stale_output.write_text("stale onboard context\n")
    os.utime(stale_output, (0, 0))

    result = run_command(
        harness_command() + ["onboard", "--no-sync"],
        cwd=target,
        env=command_env(),
    )

    assert "Onboard mutated .agent_core/:" in result.stdout
    assert "Created:" in result.stdout
    assert ".agent_core/tmp/onboard_" in result.stdout
    assert "Deleted:" in result.stdout
    assert ".agent_core/tmp/onboard_20000101_000000.md" in result.stdout
