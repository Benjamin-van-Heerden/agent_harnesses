import os
from pathlib import Path
from types import ModuleType

import pytest
from constants import GIT_USER_NAME
from helpers import HARNESS_ROOT, command_env, harness_command, init_git_project, install_harness, run_command


def test_template_onboard_reads_docs_without_indexing(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "track readme"], cwd=target)
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
    assert ".agent_core changes" in result.stdout
    assert "No .agent_core changes detected." in result.stdout
    gitignore_lines = (target / ".gitignore").read_text().splitlines()
    assert ".env" in gitignore_lines
    assert ".env/" in gitignore_lines
    assert not (target / ".agent_core" / "tmp").exists()
    assert not (target / ".agent_core" / "docs" / "data").exists()


def test_template_onboard_hides_management_commands_on_non_dev_branch(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "track readme"], cwd=target)
    install_harness(target)

    todo_path = target / ".agent_core" / "todos" / "example.md"
    todo_path.write_text(
        "---\n"
        "title: Example\n"
        "status: open\n"
        "issue_id: null\n"
        "issue_url: null\n"
        "created_at: 2026-05-22T10:00:00\n"
        "claimed_by: null\n"
        "claimed_at: null\n"
        "---\n"
        "Example body\n"
    )

    result = run_command(
        harness_command() + ["onboard", "--stdout", "--no-sync"],
        cwd=target,
        env=command_env(),
    )

    assert "No specs available. Spec creation must run from mission control on `dev`." in result.stdout
    assert "Todo claim/create/delete commands must run from mission control on `dev`." in result.stdout
    assert "Create or manage a spec if needed" not in result.stdout
    assert "Or claim a todo if directed" not in result.stdout


def test_template_onboard_expands_current_user_and_recent_logs(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "track readme"], cwd=target)
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
    assert "Current user log 1" in result.stdout
    assert "General log 6" in result.stdout
    assert "General log 5" not in result.stdout
    assert "General log 2" not in result.stdout
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
        check=False,
    )

    assert result.returncode == 1
    assert "Onboard stopped before building project context." in result.stderr
    assert "Git sync/rebase was not attempted because the working tree is dirty." in result.stderr
    assert "No onboard context file was created because local context may be stale." in result.stderr
    assert "Project" not in result.stdout


def test_template_onboard_reports_agent_core_tmp_mutations(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "track readme"], cwd=target)
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

    assert ".agent_core/tmp/onboard_" in result.stdout
    assert ".agent_core changes" not in result.stdout
    assert ".agent_core/tmp/onboard_20000101_000000.md" not in result.stdout


def test_agent_core_mutation_summary_ignores_directory_mtime_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(HARNESS_ROOT / ".agent_core" / "harness"))
    mutations = __import__("src.commands.onboard.mutations", fromlist=[""])
    assert isinstance(mutations, ModuleType)

    state_root = tmp_path / ".agent_core"
    nested_dir = state_root / "specs" / "completed"
    nested_dir.mkdir(parents=True)
    (nested_dir / "spec.md").write_text("spec body\n")

    before = mutations.snapshot_agent_core(state_root)
    os.utime(state_root / "specs")
    os.utime(nested_dir)
    after = mutations.snapshot_agent_core(state_root)

    summary = mutations.summarize_mutations(before, after)

    assert not summary.changed
