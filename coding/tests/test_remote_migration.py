import sys

from constants import SPEC_LABEL, TODO_LABEL, TODO_STATUS_LABEL
from github_helpers import authenticated_remote_url, clear_repository, client_for_token, token_or_skip
from helpers import (
    PROJECT_ROOT,
    command_env,
    configure_git,
    read_toml,
    run_command,
    write_legacy_state,
)


def _label_names(issue) -> set[str]:
    return {label.name for label in issue.labels}


def test_migrate_original_state_to_project_local_harness(tmp_path):
    token = token_or_skip()
    client = client_for_token(token)
    repo = clear_repository(client)

    target = tmp_path / "project"
    target.mkdir()
    run_command(["git", "init", "-b", "main"], cwd=target)
    configure_git(target)
    run_command(["git", "remote", "add", "origin", authenticated_remote_url(client, token)], cwd=target)

    spec_issue = repo.create_issue("Legacy Sample", "Legacy spec body")
    todo_issue = repo.create_issue("Legacy Todo", "Legacy todo body")
    write_legacy_state(target, spec_issue_id=spec_issue.number, todo_issue_id=todo_issue.number)

    run_command(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "migrate",
            str(target),
            "--to-harness",
        ],
        cwd=PROJECT_ROOT,
        env=command_env({"GITHUB_TOKEN": token}),
    )

    assert not (target / ".mem").exists()
    assert (target / ".mem.bak").is_dir()
    assert (target / ".agent_core" / "harness" / "main.py").is_file()
    assert (target / ".agent_core" / "specs" / "sample" / "spec.md").is_file()
    assert (target / ".agent_core" / "specs" / "sample" / "tasks" / "01_first.md").is_file()
    assert (target / ".agent_core" / "todos" / "open.md").is_file()
    assert (target / ".agent_core" / "todos" / "claimed" / "done.md").is_file()
    assert (target / ".agent_core" / "memories" / "pattern.md").is_file()
    assert (target / ".agent_core" / "logs" / "user_20260513_120000_session.md").is_file()
    assert (target / ".agent_core" / "docs" / "beta.md").is_file()
    assert not (target / ".agent_core" / "docs" / "core").exists()
    assert (target / "docs" / "alpha.md").is_file()
    assert (target / "docs" / "guides" / "gamma.md").is_file()
    assert not (target / ".agent_core" / "docs" / "data").exists()
    assert not (target / "docs" / "data").exists()

    config = read_toml(target / ".agent_core" / "config.toml")
    assert config["project"]["name"] == "Legacy Project"
    assert config["branches"]["dev"] == "dev"
    assert config["branches"]["main"] == "prod"
    assert config["branches"]["test"] == "stage"
    assert "generic_templates" not in config["project"]
    assert config["worktree"]["symlink_paths"] == [".agent_core/docs/data", ".claude"]
    assert (target / ".agent_core" / "user_mappings.toml").read_text() == (
        "octo = \"Octo User\"\n"
    )

    agents = (target / "AGENTS.md").read_text()
    assert agents.strip()
    assert "<MEMCONTENT>" not in agents
    assert "User notes" in agents

    refreshed_spec_issue = repo.get_issue(spec_issue.number)
    refreshed_todo_issue = repo.get_issue(todo_issue.number)
    assert _label_names(refreshed_spec_issue) == {SPEC_LABEL, TODO_STATUS_LABEL}
    assert _label_names(refreshed_todo_issue) == {TODO_LABEL, TODO_STATUS_LABEL}

    onboard = run_command(
        [
            sys.executable,
            ".agent_core/harness/main.py",
            "onboard",
            "--stdout",
        ],
        cwd=target,
        env=command_env({"GITHUB_TOKEN": token}),
    )
    assert "Beta docs" in onboard.stdout
    assert "Alpha docs" not in onboard.stdout
    assert "Sample" in onboard.stdout
