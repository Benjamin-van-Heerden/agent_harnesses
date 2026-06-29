import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

from helpers import HARNESS_ROOT, init_git_project, install_harness, read_toml, run_command


def _load_setup_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("coding_setup", HARNESS_ROOT / "setup.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_setup_preserves_state_and_avoids_removed_surfaces(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    install_harness(target)

    assert (target / ".agent_core" / "harness").is_dir()
    assert (target / ".agent_core" / "config.toml").is_file()
    assert (target / ".agent_core" / "README.md").read_text() == (HARNESS_ROOT / "README.md").read_text()
    assert (target / ".agent_core" / "user_mappings.toml").is_file()
    config = read_toml(target / ".agent_core" / "config.toml")
    assert config["worktree"]["symlink_paths"] == [".claude"]
    config_text = (target / ".agent_core" / "config.toml").read_text()
    assert "# [[runnables]]" in config_text
    assert "\n[[runnables]]" not in config_text
    gitignore_lines = (target / ".gitignore").read_text().splitlines()
    assert ".claude" in gitignore_lines
    assert ".claude/" in gitignore_lines
    assert "# Agent Core state" in gitignore_lines
    assert "!.agent_core/" in gitignore_lines
    assert "!.agent_core/**" in gitignore_lines
    assert ".agent_core/tmp/" in gitignore_lines
    assert ".agent_core/tmp/**" in gitignore_lines
    assert ".cache/pycache/" in gitignore_lines
    assert ".cache/pycache/**" in gitignore_lines
    assert not (target / ".agent_core" / "tmp").exists()
    assert (target / "AGENTS.md").read_text().strip()
    assert not list((target / ".agent_core" / "docs").glob("*.md"))

    (target / ".agent_core" / "specs" / "keep.md").write_text("state\n")
    (target / ".agent_core" / "docs" / "project_notes.md").write_text("project notes\n")
    (target / ".agent_core" / "docs" / "coding_python.md").write_text("stale python doc\n")
    (target / ".agent_core" / "docs" / "coding_general.md").write_text("retired general doc\n")
    (target / ".agent_core" / "docs" / "coding_testing.md").write_text("retired testing doc\n")
    (target / ".agent_core" / "README.md").write_text("stale readme\n")
    config_path = target / ".agent_core" / "config.toml"
    run_command(["git", "branch", "prod"], cwd=target)
    config_path.write_text('[project]\nname = "Custom"\n\n[branches]\nmain = "prod"\n')
    stale_file = target / ".agent_core" / "harness" / "stale.txt"
    stale_file.write_text("stale\n")

    run_command(["git", "checkout", "dev"], cwd=target)
    run_command([sys.executable, str(HARNESS_ROOT / "setup.py"), "--update"], cwd=target)

    config = read_toml(config_path)
    assert config["project"]["name"] == "Custom"
    assert config["branches"]["dev"] == "dev"
    assert config["branches"]["main"] == "prod"
    assert config["branches"]["test"] == "test"
    assert not stale_file.exists()
    assert (target / ".agent_core" / "specs" / "keep.md").read_text() == "state\n"
    assert (target / ".agent_core" / "docs" / "project_notes.md").read_text() == "project notes\n"
    assert (target / ".agent_core" / "docs" / "coding_python.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "coding_python.md"
    ).read_text()
    assert not (target / ".agent_core" / "docs" / "coding_general.md").exists()
    assert not (target / ".agent_core" / "docs" / "coding_testing.md").exists()
    assert (target / ".agent_core" / "README.md").read_text() == (HARNESS_ROOT / "README.md").read_text()
    gitignore_lines = (target / ".gitignore").read_text().splitlines()
    assert gitignore_lines.count(".claude") == 1
    assert gitignore_lines.count(".claude/") == 1
    assert gitignore_lines.count("# Agent Core state") == 1
    assert gitignore_lines.count("!.agent_core/") == 1
    assert gitignore_lines.count("!.agent_core/**") == 1
    assert gitignore_lines.count(".agent_core/tmp/") == 1
    assert gitignore_lines.count(".agent_core/tmp/**") == 1
    assert gitignore_lines.count(".cache/pycache/") == 1
    assert gitignore_lines.count(".cache/pycache/**") == 1
    assert not (target / ".agent_core" / "tmp").exists()

    harness_text = "\n".join(
        path.read_text(errors="ignore")
        for path in (HARNESS_ROOT / ".agent_core" / "harness").rglob("*")
        if path.is_file()
    )
    removed_patterns = [
        r"\badr\b",
        r"\badrs\b",
        r"architecture decision",
        r"\bchromadb\b",
        r"\bagno\b",
        r"\bopenai\b",
        r"\bvoyage\b",
        r"\bunstructured\b",
        r"\btextual\b",
        r"global_config",
        r"~/\.config",
    ]
    lowered = harness_text.lower()
    for pattern in removed_patterns:
        assert re.search(pattern, lowered) is None


def test_setup_updates_managed_harness_without_replacing_directory(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target)
    run_command(["git", "checkout", "dev"], cwd=target)
    harness_main = target / ".agent_core" / "harness" / "main.py"
    original_mtime = harness_main.stat().st_mtime_ns
    stale_file = target / ".agent_core" / "harness" / "stale.txt"
    stale_dir = target / ".agent_core" / "harness" / "stale_dir"
    stale_dir.mkdir()
    stale_file.write_text("stale\n")
    (stale_dir / "old.txt").write_text("old\n")

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py"), "--update"], cwd=target)

    assert harness_main.stat().st_mtime_ns == original_mtime
    assert not stale_file.exists()
    assert not stale_dir.exists()
    assert "Removed stale managed file: .agent_core/harness/stale.txt" in result.stdout
    assert "Removed stale managed file: .agent_core/harness/stale_dir/old.txt" in result.stdout
    assert "Removed stale managed directory: .agent_core/harness/stale_dir" in result.stdout


def test_setup_replaces_legacy_agents_core_block(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    (target / "AGENTS.md").write_text(
        "<AGENT_CORE>\nOld managed instructions\n</AGENT_CORE>\n\nUser notes\n"
    )
    run_command(["git", "add", "AGENTS.md"], cwd=target)
    run_command(["git", "commit", "-m", "add project agents"], cwd=target)

    install_harness(target)

    content = (target / "AGENTS.md").read_text()
    assert "<core_instructions>" in content
    assert "</core_instructions>" in content
    assert "<AGENT_CORE>" not in content
    assert "</AGENT_CORE>" not in content
    assert "Old managed instructions" not in content
    assert "User notes" in content


def test_sync_managed_directory_ignores_python_cache_artifacts(tmp_path: Path) -> None:
    setup = _load_setup_module()
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "__pycache__").mkdir(parents=True)
    (source / "pkg" / "__pycache__").mkdir(parents=True)
    (source / "pkg").mkdir(exist_ok=True)
    (source / "pkg" / "module.py").write_text("VALUE = 1\n")
    (source / "__pycache__" / "setup.cpython-314.pyc").write_bytes(b"cache")
    (source / "pkg" / "__pycache__" / "module.cpython-314.pyc").write_bytes(b"cache")

    (target / "__pycache__").mkdir(parents=True)
    (target / "pkg" / "__pycache__").mkdir(parents=True)
    (target / "__pycache__" / "stale.cpython-314.pyc").write_bytes(b"stale")
    (target / "pkg" / "__pycache__" / "stale.cpython-314.pyc").write_bytes(b"stale")

    setup.sync_managed_directory(source, target, "target")

    assert (target / "pkg" / "module.py").read_text() == "VALUE = 1\n"
    assert not (target / "__pycache__").exists()
    assert not (target / "pkg" / "__pycache__").exists()


def test_setup_creates_missing_configured_protected_branches(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    run_command(["git", "init", "-b", "main"], cwd=target)
    run_command(["git", "config", "user.name", "Harness Test User"], cwd=target)
    run_command(["git", "config", "user.email", "harness@example.com"], cwd=target)
    run_command(["git", "commit", "--allow-empty", "-m", "initial commit"], cwd=target)

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target)

    assert result.returncode == 0
    assert "Created local protected branch: dev" in result.stdout
    assert "Created local protected branch: test" in result.stdout
    assert (target / ".agent_core" / "harness").exists()
    branches = run_command(["git", "branch", "--list"], cwd=target).stdout
    assert "dev" in branches
    assert "test" in branches


def test_setup_installs_commits_pushes_and_checks_out_dev_with_origin(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    run_command(["git", "init", "--bare", remote.as_posix()], cwd=tmp_path)

    target = tmp_path / "project"
    target.mkdir()
    run_command(["git", "init", "-b", "main"], cwd=target)
    run_command(["git", "config", "user.name", "Harness Test User"], cwd=target)
    run_command(["git", "config", "user.email", "harness@example.com"], cwd=target)
    run_command(["git", "commit", "--allow-empty", "-m", "initial commit"], cwd=target)
    run_command(["git", "remote", "add", "origin", remote.as_posix()], cwd=target)
    run_command(["git", "push", "-u", "origin", "main"], cwd=target)

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target)

    assert result.returncode == 0
    assert 'Created commit on main: "install agent harness"' in result.stdout
    assert "Pushed main to origin." in result.stdout
    assert "Pushed test to origin." in result.stdout
    assert "Pushed dev to origin." in result.stdout
    assert "Checked out mission-control branch: dev" in result.stdout
    assert run_command(["git", "branch", "--show-current"], cwd=target).stdout.strip() == "dev"
    assert run_command(["git", "status", "--porcelain"], cwd=target).stdout == ""
    assert run_command(["git", "log", "-1", "--format=%s", "main"], cwd=target).stdout.strip() == "install agent harness"
    assert run_command(["git", "show", "origin/test:AGENTS.md"], cwd=target).stdout.startswith("<core_instructions>")
    assert run_command(["git", "show", "origin/dev:.agent_core/config.toml"], cwd=target).stdout


def test_setup_refuses_dirty_fresh_install_before_writing_files(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    run_command(["git", "init", "-b", "main"], cwd=target)
    run_command(["git", "config", "user.name", "Harness Test User"], cwd=target)
    run_command(["git", "config", "user.email", "harness@example.com"], cwd=target)
    run_command(["git", "commit", "--allow-empty", "-m", "initial commit"], cwd=target)
    (target / "README.md").write_text("# Dirty\n")

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target, check=False)

    assert result.returncode == 1
    assert "cannot install the agent harness with a dirty working tree" in result.stderr
    assert not (target / ".agent_core").exists()


def test_setup_refuses_fresh_install_from_non_main_before_writing_files(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target, branch="dev")

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target, check=False)

    assert result.returncode == 1
    assert "agent harness install must run from 'main'. Current branch: dev" in result.stderr
    assert not (target / ".agent_core").exists()


def test_setup_uninstall_requires_obscured_confirmation(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)

    result = subprocess.run(
        [sys.executable, str(HARNESS_ROOT / "setup.py"), "--uninstall"],
        cwd=target,
        input="not it\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "exact uninstall confirmation phrase" in result.stdout
    assert "I am sure" not in result.stdout
    assert "I am sure" not in result.stderr
    assert (target / ".agent_core").exists()


def test_setup_uninstall_removes_local_harness_state_and_branches(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)

    result = subprocess.run(
        [sys.executable, str(HARNESS_ROOT / "setup.py"), "--uninstall"],
        cwd=target,
        input="I am sure\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Uninstalled project-local harness." in result.stdout
    assert "I am sure" not in result.stdout
    assert not (target / ".agent_core").exists()
    assert not (target / "AGENTS.md").exists()
    assert not (target / "CLAUDE.md").exists()
    assert not (target / ".gitignore").exists()
    branches = run_command(["git", "branch", "--format=%(refname:short)"], cwd=target).stdout.splitlines()
    assert branches == ["main"]
    assert run_command(["git", "log", "-1", "--format=%s"], cwd=target).stdout.strip() == "uninstall agent harness"


def test_setup_does_not_activate_commented_files_config(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '''[project]
name = "Commented Files"
description = """
Project description.
"""

# Files to include in onboard output
# [[files]]
# path = "README.md"
# description = "Project overview and setup instructions"

[branches]
dev = "dev"
test = "test"
main = "main"
'''
    )
    run_command(["git", "add", ".agent_core/config.toml"], cwd=target)
    run_command(["git", "commit", "-m", "add agent config"], cwd=target)

    install_harness(target)

    content = config_path.read_text()
    assert "# [[files]]" in content
    assert "\n[[files]]" not in content


def test_setup_injects_commented_optional_onboard_config_blocks(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '''[project]
name = "Existing Project"
description = "Project description."

[worktree]
symlink_paths = [".claude"]

[branches]
dev = "dev"
test = "test"
main = "main"
'''
    )
    run_command(["git", "add", ".agent_core/config.toml"], cwd=target)
    run_command(["git", "commit", "-m", "add agent config"], cwd=target)

    install_harness(target)

    content = config_path.read_text()
    assert "# [[files]]" in content
    assert "# [[tree_dirs]]" in content
    assert "# [[runnables]]" in content
    assert '# name = "Generated project context"' in content
    assert "\n[[files]]" not in content
    assert "\n[[tree_dirs]]" not in content
    assert "\n[[runnables]]" not in content


def test_setup_updates_existing_commented_runnable_scaffold_with_name(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '''[project]
name = "Existing Project"
description = "Project description."

# Commands whose output is included in onboard output
# [[runnables]]
# command = "python -m your_tool --print-context"
# description = "Generated project context"
# timeout_seconds = 60

[worktree]
symlink_paths = [".claude"]

[branches]
dev = "dev"
test = "test"
main = "main"
'''
    )
    run_command(["git", "add", ".agent_core/config.toml"], cwd=target)
    run_command(["git", "commit", "-m", "add agent config"], cwd=target)

    install_harness(target)

    content = config_path.read_text()
    assert "# [[runnables]]\n# name = \"Generated project context\"\n# command" in content
    assert "\n[[runnables]]" not in content


def test_setup_does_not_activate_commented_required_config(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '''# [project]
# name = "Commented Project"
# description = "Commented description"

# [worktree]
# symlink_paths = [".custom_link"]

# [branches]
# dev = "develop"
# test = "staging"
# main = "production"
'''
    )
    run_command(["git", "add", ".agent_core/config.toml"], cwd=target)
    run_command(["git", "commit", "-m", "add invalid agent config"], cwd=target)

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target, check=False)

    assert result.returncode == 1
    content = config_path.read_text()
    assert "# [project]" in content
    assert "\n[project]" not in content
    assert "# [worktree]" in content
    assert "\n[worktree]" not in content
    assert "# [branches]" in content
    assert "\n[branches]" not in content


def test_setup_ignores_configured_symlink_paths(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '''[project]
name = "Symlink Ignores"
description = "Project description."

[worktree]
symlink_paths = [".custom_link", "nested/cache/"]

[branches]
dev = "dev"
test = "test"
main = "main"
'''
    )
    (target / ".gitignore").write_text(".custom_link\n")
    run_command(["git", "add", ".agent_core/config.toml", ".gitignore"], cwd=target)
    run_command(["git", "commit", "-m", "add agent config"], cwd=target)

    install_harness(target)

    content = config_path.read_text()
    assert "# Project-root relative paths to symlink from the main checkout into spec worktrees." in content
    assert 'symlink_paths = [".custom_link", "nested/cache/"]' in content
    lines = (target / ".gitignore").read_text().splitlines()
    assert lines.count(".custom_link") == 1
    assert lines.count(".custom_link/") == 1
    assert lines.count("nested/cache") == 1
    assert lines.count("nested/cache/") == 1


def test_setup_applies_agent_core_state_gitignore_patch_after_broad_ignores(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    (target / ".gitignore").write_text(".agent_core/\nconfig/\n")
    run_command(["git", "add", ".gitignore"], cwd=target)
    run_command(["git", "commit", "-m", "add broad ignores"], cwd=target)

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target)

    lines = (target / ".gitignore").read_text().splitlines()
    assert lines[-7:] == [
        "# Agent Core state",
        "!.agent_core/",
        "!.agent_core/**",
        ".agent_core/tmp/",
        ".agent_core/tmp/**",
        ".cache/pycache/",
        ".cache/pycache/**",
    ]
    assert "Applied .gitignore patch: ensured Agent Core state is tracked except .agent_core/tmp/ and .cache/pycache/ is ignored." in result.stdout
    assert run_command(["git", "check-ignore", "--no-index", ".agent_core/config.toml"], cwd=target, check=False).returncode == 1
    assert run_command(["git", "check-ignore", "--no-index", ".agent_core/tmp/onboard.md"], cwd=target, check=False).returncode == 0
    assert run_command(["git", "check-ignore", "--no-index", ".cache/pycache/example.pyc"], cwd=target, check=False).returncode == 0


def test_setup_allows_python_pycache_prefix_artifact_before_gitignore_patch(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    cache_file = target / ".cache" / "pycache" / "example.pyc"
    cache_file.parent.mkdir(parents=True)
    cache_file.write_bytes(b"cache")

    result = run_command([sys.executable, str(HARNESS_ROOT / "setup.py")], cwd=target)

    assert "Applied .gitignore patch: ensured Agent Core state is tracked except .agent_core/tmp/ and .cache/pycache/ is ignored." in result.stdout
    assert run_command(["git", "check-ignore", "--no-index", ".cache/pycache/example.pyc"], cwd=target, check=False).returncode == 0


def test_setup_config_patch_registry_updates_comments_without_resetting_values(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    config_path = target / ".agent_core" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '''[project]
name = "Patch Registry"
description = "Project description."

[worktree]
# Paths to symlink into worktrees instead of copying
symlink_paths = [".custom_link"]

[branches]
dev = "dev"
test = "test"
main = "main"
'''
    )
    run_command(["git", "add", ".agent_core/config.toml"], cwd=target)
    run_command(["git", "commit", "-m", "add agent config"], cwd=target)

    install_harness(target)
    install_harness(target)

    content = config_path.read_text()
    assert "# Paths to symlink into worktrees instead of copying" not in content
    assert content.count("# Project-root relative paths to symlink from the main checkout into spec worktrees.") == 1
    assert 'symlink_paths = [".custom_link"]' in content


def test_setup_optional_docs_commands_manage_project_local_docs(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()

    available = run_command([sys.executable, str(HARNESS_ROOT / "setup.py"), "docs", "list"], cwd=target)
    expected_slugs = sorted(path.stem for path in (HARNESS_ROOT / "optional_docs").glob("*.md"))
    assert available.stdout.splitlines() == expected_slugs

    run_command(
        [
            sys.executable,
            str(HARNESS_ROOT / "setup.py"),
            "docs",
            "add",
            "coding_python",
            "coding_rust",
        ],
        cwd=target,
    )
    docs_dir = target / ".agent_core" / "docs"
    assert (docs_dir / "coding_python.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "coding_python.md"
    ).read_text()
    assert (docs_dir / "coding_rust.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "coding_rust.md"
    ).read_text()

    (docs_dir / "coding_python.md").write_text("stale\n")
    run_command([sys.executable, str(HARNESS_ROOT / "setup.py"), "docs", "update"], cwd=target)
    assert (docs_dir / "coding_python.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "coding_python.md"
    ).read_text()

    (docs_dir / "coding_rust.md").write_text("stale\n")
    run_command(
        [sys.executable, str(HARNESS_ROOT / "setup.py"), "docs", "update", "coding_rust"],
        cwd=target,
    )
    assert (docs_dir / "coding_rust.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "coding_rust.md"
    ).read_text()
