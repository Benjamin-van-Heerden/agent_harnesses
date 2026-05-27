import sys
from pathlib import Path

from helpers import harness_command, run_command, run_setup


def test_compile_command_outputs_p_pdf_and_focus_classifies_pdfs(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from pathlib import Path

from src.state.clients import create_client
from src.state.matters import create_matter

create_client("smith", "Smith Corp", "entity")
matter = create_matter("smith", "litigation", "compile_test", "normal", "hourly")
Path("src/templates/components/style.typ").write_text("#let marker = [Hello]")
(matter / "draft.typ").write_text('#import "../../../../../src/templates/components/style.typ": marker\\n#marker')
(matter / "source.pdf").write_text("external pdf")
""".strip()
    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )
    matter_dir = next((target / "ZZ_CLIENTS" / "SMITH" / "matters" / "open").iterdir())

    harness = harness_command()
    source = matter_dir / "draft.typ"
    compiled = run_command(
        [*harness, "compile", str(source.relative_to(target))], cwd=target
    )
    assert "Compiled Typst source:" in compiled.stdout
    assert "PDF output: ZZ_CLIENTS/SMITH/matters/open/" in compiled.stdout
    assert "draft.p.pdf" in compiled.stdout
    assert (matter_dir / "draft.p.pdf").is_file()

    focus = run_command([*harness, "matter", "focus", "compile_test"], cwd=target)
    assert "Typst drafts: 1" in focus.stdout
    assert "Generated PDF outputs: 1" in focus.stdout
    assert "Other PDFs: 1" in focus.stdout
    assert "Typst source: ZZ_CLIENTS/SMITH/matters/open/" in focus.stdout
    assert "Generated PDF: ZZ_CLIENTS/SMITH/matters/open/" in focus.stdout
    assert "Other PDF: ZZ_CLIENTS/SMITH/matters/open/" in focus.stdout
