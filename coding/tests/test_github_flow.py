import re
import shutil
from pathlib import Path

from conftest import RemoteHarnessProject
from constants import SPEC_LABEL, TODO_LABEL, TODO_STATUS_LABEL
from helpers import command_env, harness_command, run_command


def _frontmatter_value(path: Path, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", path.read_text(), re.MULTILINE)
    if match is None:
        return None
    return match.group(1).strip().strip("'\"")


def _slugify(value: str) -> str:
    slug = value.lower()
    slug = re.sub(r"[\s\-]+", "_", slug)
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    slug = re.sub(r"_+", "_", slug)
    return slug.strip("_")


def test_remote_issue_sync_creates_and_imports_state(
    remote_harness_project: RemoteHarnessProject,
) -> None:
    project_path = remote_harness_project.path
    repo = remote_harness_project.repo
    token = remote_harness_project.token
    command = harness_command()
    env = command_env({"GITHUB_TOKEN": token})

    run_command(command + ["spec", "new", "Remote Sync Spec", "--body", "Remote body"], cwd=project_path, env=env)
    run_command(command + ["todo", "new", "Remote Sync Todo", "Todo body"], cwd=project_path, env=env)
    run_command(command + ["sync", "issues"], cwd=project_path, env=env)

    spec_file = project_path / ".agent_core" / "specs" / "remote_sync_spec" / "spec.md"
    todo_file = project_path / ".agent_core" / "todos" / "remote_sync_todo.md"
    spec_issue_id = _frontmatter_value(spec_file, "issue_id")
    todo_issue_id = _frontmatter_value(todo_file, "issue_id")
    assert spec_issue_id is not None
    assert todo_issue_id is not None
    assert repo.get_issue(int(spec_issue_id)).title == "Remote Sync Spec"
    assert repo.get_issue(int(todo_issue_id)).title == "Remote Sync Todo"

    repo.create_issue("Imported Remote Spec", "Imported body", labels=[SPEC_LABEL, TODO_STATUS_LABEL])
    repo.create_issue("Imported Remote Todo", "Imported todo body", labels=[TODO_LABEL, TODO_STATUS_LABEL])
    run_command(command + ["sync", "issues"], cwd=project_path, env=env)

    assert (project_path / ".agent_core" / "specs" / "imported_remote_spec" / "spec.md").is_file()
    assert (project_path / ".agent_core" / "todos" / "imported_remote_todo.md").is_file()


def test_todo_new_creates_linked_issue_and_claim_closes_it(
    remote_harness_project: RemoteHarnessProject,
) -> None:
    project_path = remote_harness_project.path
    repo = remote_harness_project.repo
    token = remote_harness_project.token
    command = harness_command()
    env = command_env({"GITHUB_TOKEN": token})

    run_command(command + ["todo", "new", "Linked Remote Todo", "Linked todo body"], cwd=project_path, env=env)

    todo_file = project_path / ".agent_core" / "todos" / "linked_remote_todo.md"
    issue_id = _frontmatter_value(todo_file, "issue_id")
    issue_url = _frontmatter_value(todo_file, "issue_url")
    assert issue_id is not None
    assert issue_url is not None
    assert run_command(["git", "status", "--porcelain"], cwd=project_path).stdout == ""

    issue = repo.get_issue(int(issue_id))
    assert issue.title == "Linked Remote Todo"
    assert issue.body == "Linked todo body"
    assert issue.state == "open"
    assert {label.name for label in issue.labels} == {TODO_LABEL, TODO_STATUS_LABEL}

    run_command(
        command + ["todo", "claim", "linked_remote_todo", "harness-test-user"],
        cwd=project_path,
        env=env,
    )

    claimed_file = project_path / ".agent_core" / "todos" / "claimed" / "linked_remote_todo.md"
    assert claimed_file.is_file()
    assert _frontmatter_value(claimed_file, "status") == "claimed"
    assert _frontmatter_value(claimed_file, "claimed_by") == "harness-test-user"

    closed_issue = repo.get_issue(int(issue_id))
    assert closed_issue.state == "closed"
    assert {label.name for label in closed_issue.labels} == {TODO_LABEL, "status:completed"}
    assert list(closed_issue.get_comments())[-1].body == (
        "Todo claimed by harness-test-user via `todo claim`."
    )


def test_remote_assignment_completion_and_merge_flow(
    remote_harness_project: RemoteHarnessProject,
) -> None:
    project_path = remote_harness_project.path
    repo = remote_harness_project.repo
    token = remote_harness_project.token
    command = harness_command()
    env = command_env({"GITHUB_TOKEN": token})

    run_command(command + ["spec", "new", "Remote Lifecycle", "--body", "Lifecycle body"], cwd=project_path, env=env)
    run_command(command + ["task", "new", "remote_lifecycle", "Finish It", "Task body"], cwd=project_path, env=env)
    run_command(command + ["sync", "issues"], cwd=project_path, env=env)
    run_command(["git", "add", "."], cwd=project_path)
    run_command(["git", "commit", "-m", "record remote lifecycle spec"], cwd=project_path)
    run_command(["git", "push", "origin", "dev"], cwd=project_path)

    run_command(command + ["spec", "assign", "remote_lifecycle"], cwd=project_path, env=env)
    worktree_path = project_path.parent / "project-worktrees" / "remote_lifecycle"
    assert worktree_path.is_dir()

    run_command(command + ["task", "complete", "remote_lifecycle", "finish_it", "Done"], cwd=worktree_path, env=env)
    run_command(command + ["spec", "complete", "remote_lifecycle", "finish lifecycle"], cwd=worktree_path, env=env)

    worktree_spec = worktree_path / ".agent_core" / "specs" / "remote_lifecycle" / "spec.md"
    pull_url = _frontmatter_value(worktree_spec, "pr_url")
    assert pull_url is not None
    branch = f"dev-{_slugify(repo.owner.login)}-remote_lifecycle"
    assert list(repo.get_pulls(state="open", head=f"{repo.owner.login}:{branch}"))

    main_spec = project_path / ".agent_core" / "specs" / "remote_lifecycle" / "spec.md"
    shutil.copy2(worktree_spec, main_spec)
    run_command(command + ["merge", "pr", "remote_lifecycle", "--message", "merge lifecycle"], cwd=project_path, env=env)

    assert (project_path / ".agent_core" / "specs" / "completed" / "remote_lifecycle" / "spec.md").is_file()
    assert not worktree_path.exists()
