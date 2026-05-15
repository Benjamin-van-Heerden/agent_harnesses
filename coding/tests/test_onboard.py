from __future__ import annotations

from helpers import command_env, harness_command, install_harness, run_command


def test_template_onboard_reads_docs_without_indexing(tmp_path):
    target = tmp_path / "project"
    target.mkdir()
    (target / "README.md").write_text("# Project\n")
    install_harness(target)

    docs_dir = target / ".agent_core" / "docs"
    (docs_dir / "nested").mkdir()
    (docs_dir / "alpha.md").write_text("Alpha doc body\n")
    (docs_dir / "nested" / "beta.md").write_text("Beta doc body\n")

    result = run_command(
        harness_command() + ["onboard", "--stdout"],
        cwd=target,
        env=command_env(),
    )

    assert "Alpha doc body" in result.stdout
    assert "Beta doc body" in result.stdout
    assert not (target / ".agent_core" / "tmp").exists()
    assert not (target / ".agent_core" / "docs" / "data").exists()
