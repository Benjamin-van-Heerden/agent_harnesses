from pathlib import Path

from helpers import (
    command_env,
    harness_command,
    init_git_project,
    install_harness,
    markdown_body,
    read_frontmatter,
    run_command,
)


def test_installed_harness_command_smoke(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "add readme"], cwd=target)
    install_harness(target)
    run_command(["git", "checkout", "dev"], cwd=target)

    command = harness_command()
    env = command_env({"GITHUB_TOKEN": ""})

    run_command(command + ["spec", "new", "Smoke Spec", "--body", "Smoke spec body"], cwd=target, env=env)
    run_command(command + ["task", "new", "First Task", "Task body", "--spec", "smoke_spec"], cwd=target, env=env)
    run_command(
        command
        + [
            "task",
            "complete",
            "first_task",
            "Implemented in smoke test",
            "--spec",
            "smoke_spec",
            "--user-gave-explicit-permission",
        ],
        cwd=target,
        env=env,
    )
    run_command(command + ["memory", "new", "Smoke Memory", "Memory body"], cwd=target, env=env)
    run_command(command + ["log", "new", "--spec-slug", "smoke_spec"], cwd=target, env=env)

    spec_file = target / ".agent_core" / "specs" / "smoke_spec" / "spec.md"
    task_file = target / ".agent_core" / "specs" / "smoke_spec" / "tasks" / "01_first_task.md"
    memory_file = target / ".agent_core" / "memories" / "smoke_memory.md"
    log_files = list((target / ".agent_core" / "logs").glob("harness_test_user_*_session.md"))

    assert spec_file.is_file()
    assert markdown_body(spec_file).strip() == "Smoke spec body"
    assert task_file.is_file()
    assert read_frontmatter(task_file)["status"] == "completed"
    assert markdown_body(task_file).strip() == "Task body\n\n## Completion Notes\n\nImplemented in smoke test"
    assert memory_file.is_file()
    assert markdown_body(memory_file).strip() == "Memory body"
    assert len(log_files) == 1
    assert not (target / ".mem").exists()

    onboard = run_command(command + ["onboard", "--stdout", "--no-sync"], cwd=target, env=env)
    assert "Smoke Spec" in onboard.stdout
    assert "Tasks: 1/1 completed" in onboard.stdout
    assert "Smoke Memory" in onboard.stdout
