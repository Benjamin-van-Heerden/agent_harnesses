from pathlib import Path

from helpers import command_env, harness_command, init_git_project, install_harness, run_command


def test_installed_harness_local_worktree_commands(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    run_command(["git", "add", "."], cwd=target)
    run_command(["git", "commit", "-m", "initial harness state"], cwd=target)

    command = harness_command()
    env = command_env({"GITHUB_TOKEN": ""})

    protected_delete = run_command(
        command + ["cleanup", "branch", "main", "--force"],
        cwd=target,
        env=env,
        check=False,
    )
    assert protected_delete.returncode == 1
    protected_branch = run_command(
        ["git", "show-ref", "--verify", "refs/heads/main"],
        cwd=target,
        check=False,
    )
    assert protected_branch.returncode == 0

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
    removed_branch = run_command(
        ["git", "show-ref", "--verify", "refs/heads/smoke/worktree"],
        cwd=target,
        check=False,
    )
    assert removed_branch.returncode != 0
