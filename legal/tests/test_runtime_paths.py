import sys
from pathlib import Path

from helpers import (
    LEGAL_ROOT,
    assert_ascii_safe,
    harness_command,
    run_command,
    run_setup,
)


def test_runtime_dependency_guidance_requires_git_and_typst(tmp_path: Path) -> None:
    script = """
import deps

deps.command_version_available = lambda command: False
deps.require_dependencies()
""".strip()

    result = run_command(
        [sys.executable, "-B", "-c", script],
        cwd=tmp_path,
        check=False,
        extra_env={"PYTHONPATH": str(LEGAL_ROOT / ".agent_core" / "harness")},
    )

    assert result.returncode == 1
    assert "Missing required dependencies." in result.stderr
    assert "git: required for local practice-state checkpoints" in result.stderr
    assert "typst: required for legal document compilation" in result.stderr
    assert "winget install --id Typst.Typst" in result.stderr
    assert_ascii_safe(result.stderr)


def test_installed_runtime_foundation_commands_run(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()
    help_result = run_command([*harness, "--help"], cwd=target)
    assert "client" in help_result.stdout
    assert "matter" in help_result.stdout
    assert "chronology" in help_result.stdout
    assert "obligation" in help_result.stdout
    assert "deadline" not in help_result.stdout
    assert "record" not in help_result.stdout
    assert "lint" in help_result.stdout

    paths_result = run_command([*harness, "paths"], cwd=target)
    assert f"Project root: {target}" in paths_result.stdout
    assert f"State root: {target / '.praxis'}" in paths_result.stdout
    assert f"Harness root: {target / '.praxis' / 'harness'}" in paths_result.stdout
    assert f"Core docs root: {target / '.praxis' / 'core_docs'}" in paths_result.stdout
    assert f"Docs root: {target / '.praxis' / 'docs'}" in paths_result.stdout
    assert (
        f"Local context root: {target / '.praxis' / 'local_context'}"
        in paths_result.stdout
    )
    assert f"Clients root: {target / 'ZZ_CLIENTS'}" in paths_result.stdout
    assert f"WIP root: {target / 'WIP'}" in paths_result.stdout
    assert_ascii_safe(paths_result.stdout)

    config_result = run_command([*harness, "config", "show"], cwd=target)
    assert "Harness: legal" in config_result.stdout
    assert "Local git snapshots: True" in config_result.stdout
    assert_ascii_safe(config_result.stdout)
