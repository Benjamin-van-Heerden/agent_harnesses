import re

from helpers import HARNESS_ROOT, init_git_project, install_harness, read_toml, run_command


def test_template_setup_preserves_state_and_avoids_removed_surfaces(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)

    install_harness(target)

    assert (target / ".agent_core" / "harness").is_dir()
    assert (target / ".agent_core" / "config.toml").is_file()
    assert (target / ".agent_core" / "user_mappings.toml").is_file()
    gitignore_lines = (target / ".gitignore").read_text().splitlines()
    assert ".agent_core/docs/data" in gitignore_lines
    assert ".agent_core/docs/data/" in gitignore_lines
    assert ".claude" in gitignore_lines
    assert ".claude/" in gitignore_lines
    assert not (target / ".agent_core" / "tmp").exists()
    assert (target / "AGENTS.md").read_text().strip()
    assert (target / ".agent_core" / "docs" / "general.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "general.md"
    ).read_text()
    assert (target / ".agent_core" / "docs" / "testing.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "testing.md"
    ).read_text()

    (target / ".agent_core" / "specs" / "keep.md").write_text("state\n")
    (target / ".agent_core" / "docs" / "general.md").write_text("project notes\n")
    config_path = target / ".agent_core" / "config.toml"
    run_command(["git", "branch", "prod"], cwd=target)
    config_path.write_text('[project]\nname = "Custom"\n\n[branches]\nmain = "prod"\n')
    stale_file = target / ".agent_core" / "harness" / "stale.txt"
    stale_file.write_text("stale\n")

    install_harness(target)

    config = read_toml(config_path)
    assert config["project"]["name"] == "Custom"
    assert config["branches"]["dev"] == "dev"
    assert config["branches"]["main"] == "prod"
    assert config["branches"]["test"] == "test"
    assert not stale_file.exists()
    assert (target / ".agent_core" / "specs" / "keep.md").read_text() == "state\n"
    assert (target / ".agent_core" / "docs" / "general.md").read_text() == "project notes\n"
    gitignore_lines = (target / ".gitignore").read_text().splitlines()
    assert gitignore_lines.count(".agent_core/docs/data") == 1
    assert gitignore_lines.count(".agent_core/docs/data/") == 1
    assert gitignore_lines.count(".claude") == 1
    assert gitignore_lines.count(".claude/") == 1
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


def test_setup_creates_missing_configured_protected_branches(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    run_command(["git", "init", "-b", "main"], cwd=target)
    run_command(["git", "config", "user.name", "Harness Test User"], cwd=target)
    run_command(["git", "config", "user.email", "harness@example.com"], cwd=target)
    run_command(["git", "commit", "--allow-empty", "-m", "initial commit"], cwd=target)

    result = run_command([str(HARNESS_ROOT / "setup.sh")], cwd=target)

    assert result.returncode == 0
    assert "Created local protected branch: dev" in result.stdout
    assert "Created local protected branch: test" in result.stdout
    assert (target / ".agent_core" / "harness").exists()
    branches = run_command(["git", "branch", "--list"], cwd=target).stdout
    assert "dev" in branches
    assert "test" in branches


def test_setup_does_not_activate_commented_files_config(tmp_path):
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

    install_harness(target)

    content = config_path.read_text()
    assert "# [[files]]" in content
    assert "\n[[files]]" not in content


def test_setup_does_not_activate_commented_required_config(tmp_path):
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

    result = run_command([str(HARNESS_ROOT / "setup.sh")], cwd=target, check=False)

    assert result.returncode == 1
    content = config_path.read_text()
    assert "# [project]" in content
    assert "\n[project]" not in content
    assert "# [worktree]" in content
    assert "\n[worktree]" not in content
    assert "# [branches]" in content
    assert "\n[branches]" not in content


def test_setup_ignores_configured_symlink_paths(tmp_path):
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

    install_harness(target)

    lines = (target / ".gitignore").read_text().splitlines()
    assert lines.count(".custom_link") == 1
    assert lines.count(".custom_link/") == 1
    assert lines.count("nested/cache") == 1
    assert lines.count("nested/cache/") == 1


def test_setup_optional_docs_commands_manage_project_local_docs(tmp_path):
    target = tmp_path / "project"
    target.mkdir()

    available = run_command([str(HARNESS_ROOT / "setup.sh"), "docs", "list"], cwd=target)
    expected_slugs = sorted(path.stem for path in (HARNESS_ROOT / "optional_docs").glob("*.md"))
    assert available.stdout.splitlines() == expected_slugs

    run_command([str(HARNESS_ROOT / "setup.sh"), "docs", "add", "python", "testing"], cwd=target)
    docs_dir = target / ".agent_core" / "docs"
    assert (docs_dir / "python.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "python.md"
    ).read_text()
    assert (docs_dir / "testing.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "testing.md"
    ).read_text()

    (docs_dir / "python.md").write_text("stale\n")
    run_command([str(HARNESS_ROOT / "setup.sh"), "docs", "update"], cwd=target)
    assert (docs_dir / "python.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "python.md"
    ).read_text()

    (docs_dir / "testing.md").write_text("stale\n")
    run_command([str(HARNESS_ROOT / "setup.sh"), "docs", "update", "testing"], cwd=target)
    assert (docs_dir / "testing.md").read_text() == (
        HARNESS_ROOT / "optional_docs" / "testing.md"
    ).read_text()
