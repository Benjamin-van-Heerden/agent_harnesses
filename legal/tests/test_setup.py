import sys
from pathlib import Path

from helpers import LEGAL_ROOT, assert_ascii_safe, read_toml, run_command, run_setup


def test_setup_requires_git_and_typst_with_install_guidance(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    empty_path = tmp_path / "empty_path"
    empty_path.mkdir()

    result = run_command(
        [sys.executable, "-B", str(LEGAL_ROOT / "setup.py")],
        cwd=target,
        check=False,
        extra_env={"PATH": str(empty_path)},
    )

    assert result.returncode == 1
    assert not (target / ".agent_core").exists()
    assert not (target / ".praxis").exists()
    assert "Error: missing required external dependencies." in result.stderr
    assert (
        "Setup checks these commands with --version before installing the legal harness."
        in result.stderr
    )
    assert "Missing required command: git" in result.stderr
    assert "Missing required command: typst" in result.stderr
    assert "winget install --id Git.Git" in result.stderr
    assert "winget install --id Typst.Typst" in result.stderr
    assert_ascii_safe(result.stderr)


def test_repository_template_layout_matches_legal_harness_contract() -> None:
    template_root = LEGAL_ROOT / ".agent_core"

    assert (template_root / "core_docs" / "legal_context.typ").is_file()
    assert (template_root / "docs" / "typst_detailed_reference.typ").is_file()
    assert (template_root / "local_context" / "lawyer_profile.md").is_file()
    assert (template_root / "harness" / "templates" / "log.md").is_file()
    assert (template_root / "harness" / "templates" / "memory.md").is_file()
    assert (template_root / "harness" / "templates" / "profile.md").is_file()
    assert (template_root / "harness" / "templates" / "status.md").is_file()
    assert (template_root / "harness" / "templates" / "todo.md").is_file()
    assert not (LEGAL_ROOT / ".agent_docs").exists()
    assert not (LEGAL_ROOT / ".DS_Store").exists()


def test_setup_installs_native_harness_and_preserves_user_content(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    (target / "AGENTS.md").write_text("Existing lawyer-specific instruction.\n")

    result = run_setup(target)

    assert result.returncode == 0
    assert (target / ".praxis" / "harness" / "main.py").is_file()
    assert not (target / ".agent_core").exists()
    assert not (target / ".agent_docs").exists()
    assert (target / ".praxis" / "local_context" / "lawyer_profile.md").is_file()
    assert (target / ".praxis" / "core_docs" / "legal_context.typ").is_file()
    assert not (target / ".praxis" / "docs" / "legal_harness_function.md").exists()
    assert (
        target / ".praxis" / "docs" / "legal_harness_typst_basic_reference.typ"
    ).read_text() == (
        LEGAL_ROOT / "optional_docs" / "legal_harness_typst_basic_reference.typ"
    ).read_text()
    assert (
        target
        / ".praxis"
        / "docs"
        / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).read_text() == (
        LEGAL_ROOT
        / "optional_docs"
        / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).read_text()
    assert (
        target / ".praxis" / "docs" / "typst_detailed_reference.typ"
    ).read_text() == (
        LEGAL_ROOT / ".agent_core" / "docs" / "typst_detailed_reference.typ"
    ).read_text()
    assert not (target / ".praxis" / "docs" / "typst_basic_reference.typ").exists()
    assert not (
        target
        / ".praxis"
        / "docs"
        / "typst_soft_typesystem_and_house_rules_updated.typ"
    ).exists()
    assert (target / "src" / "types" / "Client.typ").read_text() == (
        LEGAL_ROOT / "src" / "types" / "Client.typ"
    ).read_text()
    assert (target / "ZZ_CLIENTS").is_dir()
    assert (target / "UNBOUND" / "open").is_dir()
    assert (target / "UNBOUND" / "closed").is_dir()
    assert not (target / "clients").exists()
    assert (target / "WIP" / "drafts").is_dir()
    assert (target / "WIP" / "experiments").is_dir()
    assert (
        "Matter-specific drafts belong in the matter folder"
        in (target / "WIP" / "README.md").read_text()
    )
    assert (target / "assets").is_dir()
    assert (target / "src" / "components").is_dir()
    assert not (target / "src" / "functions").exists()
    assert (target / "src" / "templates").is_dir()
    agents_text = (target / "AGENTS.md").read_text()
    assert "Existing lawyer-specific instruction." in agents_text
    assert "python -B .praxis/harness/main.py onboard" in agents_text
    assert "python -B .praxis/harness/main.py compile <source.typ>" in agents_text
    assert ".agent_core/docs/legal_harness_function.md" not in agents_text
    assert "agent_rules/commands" not in agents_text
    assert "agent_rules/scripts" not in agents_text
    assert (target / "CLAUDE.md").exists()
    assert "legal Agent Core setup" in (target / ".gitignore").read_text()
    assert "*.p.pdf" in (target / ".gitignore").read_text()
    assert (LEGAL_ROOT / "README.md").is_file()
    assert not (LEGAL_ROOT / "agent_rules").exists()
    assert not (LEGAL_ROOT / "bash_setup.sh").exists()

    config = read_toml(target / ".praxis" / "config.toml")
    assert config["harness"]["name"] == "legal"
    assert config["harness"]["update_interval_days"] == 3
    assert "last_updated_at" in config["harness"]
    assert (target / ".praxis" / "harness" / "update.py").is_file()


def test_setup_update_refreshes_managed_runtime_without_clobbering_lawyer_state(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    profile = target / ".praxis" / "local_context" / "lawyer_profile.md"
    legal_context = target / ".praxis" / "core_docs" / "legal_context.typ"
    custom_source = target / "src" / "components" / "custom.typ"
    custom_workflow = target / ".praxis" / "local_context" / "workflows" / "custom.toml"
    client_note = target / "ZZ_CLIENTS" / "SMITH" / "profile.md"
    stale_harness_file = target / ".praxis" / "harness" / "stale.txt"

    profile.write_text("lawyer profile edited by lawyer\n")
    legal_context.write_text("legal context edited by lawyer\n")
    custom_source.parent.mkdir(parents=True, exist_ok=True)
    custom_source.write_text("#let custom = true\n")
    custom_workflow.write_text("custom workflow\n")
    client_note.parent.mkdir(parents=True, exist_ok=True)
    client_note.write_text("confidential client state\n")
    stale_harness_file.write_text("stale runtime\n")
    (
        target / ".praxis" / "docs" / "legal_harness_typst_basic_reference.typ"
    ).write_text("stale managed doc\n")
    (
        target
        / ".praxis"
        / "docs"
        / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).write_text("stale soft type doc\n")
    (target / ".praxis" / "docs" / "typst_basic_reference.typ").write_text(
        "old managed doc\n"
    )
    (
        target
        / ".praxis"
        / "docs"
        / "typst_soft_typesystem_and_house_rules_updated.typ"
    ).write_text("old soft type doc\n")
    (target / ".praxis" / "docs" / "typst_detailed_reference.typ").write_text(
        "stale detailed doc\n"
    )
    (target / "src" / "types" / "Client.typ").write_text("stale managed source\n")

    result = run_setup(target, update=True)

    assert "Removed stale managed file: .praxis/harness/stale.txt" in result.stdout
    assert profile.read_text() == "lawyer profile edited by lawyer\n"
    assert legal_context.read_text() == "legal context edited by lawyer\n"
    assert custom_source.read_text() == "#let custom = true\n"
    assert custom_workflow.read_text() == "custom workflow\n"
    assert client_note.read_text() == "confidential client state\n"
    assert not stale_harness_file.exists()
    assert "Updated optional doc: legal_harness_typst_basic_reference" in result.stdout
    assert (
        "Updated managed file: .praxis/docs/typst_detailed_reference.typ"
        in result.stdout
    )
    assert (
        "Removed renamed managed doc: .praxis/docs/typst_basic_reference.typ"
        in result.stdout
    )
    assert (
        target / ".praxis" / "docs" / "legal_harness_typst_basic_reference.typ"
    ).read_text() == (
        LEGAL_ROOT / "optional_docs" / "legal_harness_typst_basic_reference.typ"
    ).read_text()
    assert (
        target
        / ".praxis"
        / "docs"
        / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).read_text() == (
        LEGAL_ROOT
        / "optional_docs"
        / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).read_text()
    assert not (target / ".praxis" / "docs" / "typst_basic_reference.typ").exists()
    assert not (
        target
        / ".praxis"
        / "docs"
        / "typst_soft_typesystem_and_house_rules_updated.typ"
    ).exists()
    assert (
        target / ".praxis" / "docs" / "typst_detailed_reference.typ"
    ).read_text() == (
        LEGAL_ROOT / ".agent_core" / "docs" / "typst_detailed_reference.typ"
    ).read_text()
    assert (target / "src" / "types" / "Client.typ").read_text() == (
        LEGAL_ROOT / "src" / "types" / "Client.typ"
    ).read_text()


def test_setup_docs_commands_manage_optional_docs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    docs_list = run_command(
        [sys.executable, "-B", str(LEGAL_ROOT / "setup.py"), "docs", "list"], cwd=target
    )
    assert "legal_harness_typst_basic_reference" in docs_list.stdout
    assert "legal_harness_function" not in docs_list.stdout

    target_doc = target / ".praxis" / "docs" / "legal_harness_typst_basic_reference.typ"
    target_doc.unlink()
    docs_add = run_command(
        [
            sys.executable,
            "-B",
            str(LEGAL_ROOT / "setup.py"),
            "docs",
            "add",
            "legal_harness_typst_basic_reference",
        ],
        cwd=target,
    )
    assert "Added optional doc: legal_harness_typst_basic_reference" in docs_add.stdout
    assert target_doc.is_file()

    target_doc.write_text("stale\n")
    docs_update = run_command(
        [sys.executable, "-B", str(LEGAL_ROOT / "setup.py"), "docs", "update"],
        cwd=target,
    )
    assert (
        "Updated optional doc: legal_harness_typst_basic_reference"
        in docs_update.stdout
    )
    assert (
        target_doc.read_text()
        == (
            LEGAL_ROOT / "optional_docs" / "legal_harness_typst_basic_reference.typ"
        ).read_text()
    )

    missing_function_doc = run_command(
        [
            sys.executable,
            "-B",
            str(LEGAL_ROOT / "setup.py"),
            "docs",
            "add",
            "legal_harness_function",
        ],
        cwd=target,
        check=False,
    )
    assert missing_function_doc.returncode == 1
    assert "unknown optional doc: legal_harness_function" in missing_function_doc.stderr
