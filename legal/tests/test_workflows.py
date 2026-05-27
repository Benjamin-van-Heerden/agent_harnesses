import sys
from pathlib import Path

from helpers import harness_command, run_command, run_setup


def test_workflow_commands_and_matter_focus_integration(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()
    created = run_command([*harness, "workflow", "new", "Litigation Flow"], cwd=target)
    assert "Created workflow: litigation_flow" in created.stdout
    workflow_file = (
        target / ".praxis" / "local_context" / "workflows" / "litigation_flow.toml"
    )
    assert workflow_file.is_file()
    assert "[[steps]]" in workflow_file.read_text()

    listed = run_command([*harness, "workflow", "list"], cwd=target)
    assert "litigation_flow\tLitigation Flow\t2" in listed.stdout

    shown = run_command([*harness, "workflow", "show", "litigation_flow"], cwd=target)
    assert "Workflow: Litigation Flow" in shown.stdout
    assert "intake\ttask" in shown.stdout

    script = """
from src.state.clients import create_client
from src.state.matters import create_matter

create_client("smith", "Smith Corp", "entity")
create_matter("smith", "litigation", "workflow_test", "normal", "hourly")
""".strip()
    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )

    linked = run_command(
        [*harness, "workflow", "link", "workflow_test", "litigation_flow"], cwd=target
    )
    assert "Linked workflow: litigation_flow" in linked.stdout
    matter_dir = next((target / "ZZ_CLIENTS" / "smith" / "matters" / "open").iterdir())
    progress_file = matter_dir / "info" / "workflow.toml"
    assert progress_file.is_file()
    progress_file.write_text(
        'completed_steps = ["intake"]\nblocked_steps = []\ncurrent_steps = []\n'
    )

    focus = run_command([*harness, "matter", "focus", "workflow_test"], cwd=target)
    assert "Workflow: Litigation Flow" in focus.stdout
    assert "Workflow progress:" in focus.stdout
    assert "Completed: intake" in focus.stdout
    assert "Current: draft" in focus.stdout
    assert "Next action: Prepare first draft" in focus.stdout
    assert "Workflow todo: Prepare the first working draft" in focus.stdout
