from constants import GIT_USER_NAME
from helpers import command_env, harness_command, init_git_project, install_harness, run_command


def test_template_onboard_reads_docs_without_indexing(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    install_harness(target)

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
    assert not (target / ".agent_core" / "tmp").exists()
    assert not (target / ".agent_core" / "docs" / "data").exists()


def test_template_onboard_expands_current_user_and_recent_logs(tmp_path):
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


def test_template_onboard_warns_and_continues_when_sync_fails(tmp_path):
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
