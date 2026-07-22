from pathlib import Path

from helpers import harness_command, init_git_project, install_harness, run_command


def test_docs_command_manages_optional_docs(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)

    available = run_command([*harness_command(), "docs", "list"], cwd=target)
    assert "coding_python: available" in available.stdout
    assert "coding_uv: available" in available.stdout

    added = run_command([*harness_command(), "docs", "add", "coding_python"], cwd=target)
    doc = target / ".agent_core" / "docs" / "coding_python.md"
    manifest = target / ".agent_core" / "optional_docs.toml"
    assert "Added optional doc: coding_python" in added.stdout
    assert doc.is_file()
    assert 'slug = "coding_python"' in manifest.read_text()
    assert "coding_python: installed" in run_command([*harness_command(), "docs", "list"], cwd=target).stdout

    catalog_doc = target / ".agent_core" / "harness" / "optional_docs" / "coding_python.md"
    catalog_doc.write_text("new catalog version\n")
    assert "coding_python: outdated" in run_command([*harness_command(), "docs", "list"], cwd=target).stdout
    run_command([*harness_command(), "docs", "update", "coding_python"], cwd=target)
    assert doc.read_text() == "new catalog version\n"

    doc.write_text("local changes\n")
    refused_update = run_command([*harness_command(), "docs", "update", "coding_python"], cwd=target, check=False)
    assert refused_update.returncode == 1
    assert "refusing to overwrite locally modified doc(s): coding_python" in refused_update.stderr
    assert doc.read_text() == "local changes\n"

    updated = run_command([*harness_command(), "docs", "update", "coding_python", "--force"], cwd=target)
    assert "Updated optional doc: coding_python" in updated.stdout
    assert doc.read_text() != "local changes\n"

    doc.write_text("more local changes\n")
    refused_remove = run_command([*harness_command(), "docs", "remove", "coding_python"], cwd=target, check=False)
    assert refused_remove.returncode == 1
    assert "refusing to remove locally modified doc(s): coding_python" in refused_remove.stderr
    assert doc.is_file()

    removed = run_command([*harness_command(), "docs", "remove", "coding_python", "--force"], cwd=target)
    assert "Removed optional doc: coding_python" in removed.stdout
    assert not doc.exists()
    assert not manifest.exists()


def test_docs_add_validates_all_slugs_before_writing(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)

    unknown = run_command(
        [*harness_command(), "docs", "add", "coding_python", "not_available"],
        cwd=target,
        check=False,
    )
    assert unknown.returncode == 1
    assert "unknown optional doc slug(s): not_available" in unknown.stderr
    assert "Available slugs:" in unknown.stderr
    assert not (target / ".agent_core" / "docs" / "coding_python.md").exists()
    assert not (target / ".agent_core" / "optional_docs.toml").exists()

    invalid = run_command([*harness_command(), "docs", "add", "coding-python"], cwd=target, check=False)
    assert invalid.returncode == 1
    assert "invalid optional doc slug(s): coding-python" in invalid.stderr
    assert not (target / ".agent_core" / "optional_docs.toml").exists()

    unmanaged = target / ".agent_core" / "docs" / "coding_python.md"
    unmanaged.write_text("project-authored content\n")
    collision = run_command([*harness_command(), "docs", "add", "coding_python"], cwd=target, check=False)
    assert collision.returncode == 1
    assert "refusing to overwrite unmanaged doc(s): coding_python" in collision.stderr
    assert unmanaged.read_text() == "project-authored content\n"


def test_docs_add_adopts_matching_unmanaged_doc(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    source = target / ".agent_core" / "harness" / "optional_docs" / "coding_python.md"
    doc = target / ".agent_core" / "docs" / "coding_python.md"
    doc.write_bytes(source.read_bytes())

    result = run_command([*harness_command(), "docs", "add", "coding_python"], cwd=target)

    assert result.returncode == 0
    assert "Added optional doc: coding_python" in result.stdout
    assert 'slug = "coding_python"' in (target / ".agent_core" / "optional_docs.toml").read_text()


def test_docs_remove_rejects_uninstalled_slug_without_partial_changes(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    run_command([*harness_command(), "docs", "add", "coding_python"], cwd=target)

    result = run_command(
        [*harness_command(), "docs", "remove", "coding_python", "coding_uv"],
        cwd=target,
        check=False,
    )

    assert result.returncode == 1
    assert "optional doc(s) are not installed: coding_uv" in result.stderr
    assert (target / ".agent_core" / "docs" / "coding_python.md").is_file()
    assert 'slug = "coding_python"' in (target / ".agent_core" / "optional_docs.toml").read_text()


def test_docs_rejects_invalid_manifest_records(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    manifest = target / ".agent_core" / "optional_docs.toml"
    manifest.write_text(
        '''[[docs]]
slug = "../outside"
source_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
'''
    )

    result = run_command([*harness_command(), "docs", "list"], cwd=target, check=False)

    assert result.returncode == 1
    assert "could not read" in result.stderr
