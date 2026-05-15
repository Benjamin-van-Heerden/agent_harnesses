from __future__ import annotations

from helpers import command_env, harness_command, init_git_project, install_harness, run_command


def test_installed_harness_local_worktree_commands(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    run_command(["git", "add", "."], cwd=target)
    run_command(["git", "commit", "-m", "initial harness state"], cwd=target)

    command = harness_command()
    env = command_env({"GITHUB_TOKEN": ""})

    status = run_command(command + ["sync", "status"], cwd=target, env=env)
    assert "Branch: main" in status.stdout

    protected_delete = run_command(
        command + ["cleanup", "branch", "main", "--force"],
        cwd=target,
        env=env,
        check=False,
    )
    assert protected_delete.returncode == 1
    assert "Refusing to delete protected branch: main" in protected_delete.stderr

    run_command(
        command + ["worktree", "create", "smoke_worktree", "smoke/worktree"],
        cwd=target,
        env=env,
    )
    worktree_path = tmp_path / "project-worktrees" / "smoke_worktree"
    assert worktree_path.is_dir()
    assert (worktree_path / ".agent_core" / "harness" / "main.py").is_file()

    listing = run_command(command + ["worktree", "list"], cwd=target, env=env)
    assert "smoke/worktree" in listing.stdout
    assert str(worktree_path) in listing.stdout

    run_command(command + ["worktree", "remove", "smoke_worktree", "--force"], cwd=target, env=env)
    assert not worktree_path.exists()

    run_command(command + ["cleanup", "branch", "smoke/worktree", "--force"], cwd=target, env=env)
    branches = run_command(["git", "branch", "--list", "smoke/worktree"], cwd=target)
    assert branches.stdout.strip() == ""
