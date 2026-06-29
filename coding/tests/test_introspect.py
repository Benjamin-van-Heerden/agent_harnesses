from pathlib import Path

from helpers import command_env, harness_command, init_git_project, install_harness, run_command


def test_introspect_structure_scaffolds_core_doc_and_instructions(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    (target / "src").mkdir()
    (target / "src" / "app.py").write_text("print('hello')\n")
    init_git_project(target)
    run_command(["git", "add", "README.md", "src/app.py"], cwd=target)
    run_command(["git", "commit", "-m", "track project files"], cwd=target)
    install_harness(target)

    result = run_command(
        harness_command() + ["introspect", "structure"],
        cwd=target,
        env=command_env(),
    )

    doc_path = target / ".agent_core" / "docs" / "codebase_and_structure.md"
    assert doc_path.is_file()
    assert doc_path.read_text().startswith("# Codebase and Structure")
    assert "Do not infer goals or intent." in doc_path.read_text()
    assert "## Tests and Verification" in doc_path.read_text()
    assert "Created introspection document: .agent_core/docs/codebase_and_structure.md" in result.stdout
    assert "./README.md" in result.stdout
    assert "./src/app.py" in result.stdout
    assert ".agent_core/harness" not in result.stdout
    assert "You must research the codebase and replace every placeholder" in result.stdout
    assert "This document is a factual repository map" in result.stdout
    assert "Do not include project goals" in result.stdout


def test_introspect_what_requires_user_interview(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    init_git_project(target)
    run_command(["git", "add", "README.md"], cwd=target)
    run_command(["git", "commit", "-m", "track readme"], cwd=target)
    install_harness(target)

    result = run_command(
        harness_command() + ["introspect", "what"],
        cwd=target,
        env=command_env(),
    )

    doc_path = target / ".agent_core" / "docs" / "what.md"
    assert doc_path.is_file()
    assert doc_path.read_text().startswith("# What Is This Project?")
    assert "Created introspection document: .agent_core/docs/what.md" in result.stdout
    assert "You must interview the user before completing the document" in result.stdout
    assert "do not proceed until they have answered" in result.stdout


def test_introspect_does_not_overwrite_existing_doc_without_force(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    doc_path = target / ".agent_core" / "docs" / "what.md"
    doc_path.write_text("custom\n")

    result = run_command(
        harness_command() + ["introspect", "what"],
        cwd=target,
        env=command_env(),
        check=False,
    )

    assert result.returncode != 0
    assert doc_path.read_text() == "custom\n"

    force_result = run_command(
        harness_command() + ["introspect", "what", "--force"],
        cwd=target,
        env=command_env(),
    )
    assert force_result.returncode == 0
    assert doc_path.read_text().startswith("# What Is This Project?")
