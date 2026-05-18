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
    install_harness(target)

    command = harness_command()
    env = command_env({"GITHUB_TOKEN": ""})

    run_command(command + ["spec", "new", "Smoke Spec", "--body", "Smoke spec body"], cwd=target, env=env)
    run_command(command + ["task", "new", "smoke_spec", "First Task", "Task body"], cwd=target, env=env)
    run_command(
        command + ["task", "complete", "smoke_spec", "first_task", "Implemented in smoke test"],
        cwd=target,
        env=env,
    )
    run_command(command + ["todo", "new", "Smoke Todo", "Todo body"], cwd=target, env=env)
    run_command(command + ["todo", "claim", "smoke_todo", "smoke-user"], cwd=target, env=env)
    run_command(command + ["todo", "new", "Open Smoke Todo", "Open todo body"], cwd=target, env=env)
    run_command(command + ["memory", "new", "Smoke Memory", "Memory body"], cwd=target, env=env)
    run_command(command + ["log", "new", "--spec-slug", "smoke_spec"], cwd=target, env=env)

    spec_file = target / ".agent_core" / "specs" / "smoke_spec" / "spec.md"
    task_file = target / ".agent_core" / "specs" / "smoke_spec" / "tasks" / "01_first_task.md"
    todo_file = target / ".agent_core" / "todos" / "claimed" / "smoke_todo.md"
    memory_file = target / ".agent_core" / "memories" / "smoke_memory.md"
    log_files = list((target / ".agent_core" / "logs").glob("harness_test_user_*_session.md"))

    assert spec_file.is_file()
    assert markdown_body(spec_file).strip() == "Smoke spec body"
    assert task_file.is_file()
    assert read_frontmatter(task_file)["status"] == "completed"
    assert markdown_body(task_file).strip() == "Task body\n\n## Completion Notes\n\nImplemented in smoke test"
    assert todo_file.is_file()
    assert read_frontmatter(todo_file)["status"] == "claimed"
    assert memory_file.is_file()
    assert markdown_body(memory_file).strip() == "Memory body"
    assert len(log_files) == 1
    assert not (target / ".mem").exists()

    onboard = run_command(command + ["onboard", "--stdout", "--no-sync"], cwd=target, env=env)
    assert "Smoke Spec" in onboard.stdout
    assert "First Task" in onboard.stdout
    assert "Open Smoke Todo" in onboard.stdout
    assert "Smoke Memory" in onboard.stdout
