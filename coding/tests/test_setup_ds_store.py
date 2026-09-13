import sys
from pathlib import Path

from helpers import HARNESS_ROOT, init_git_project, install_harness, run_command


def test_setup_ignores_ds_store_on_install_and_existing_project_update(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    init_git_project(target)
    install_harness(target)
    run_command(["git", "checkout", "dev"], cwd=target)

    gitignore_file = target / ".gitignore"
    patches_file = target / ".agent_core" / "patches.toml"
    ignore_entry = ".agent_core/**/.DS_Store"
    patch_id = "0006_agent_core_ds_store_gitignore"
    ds_store_paths = [".agent_core/.DS_Store", ".agent_core/docs/.DS_Store", ".agent_core/specs/example/tasks/.DS_Store"]
    for path in ds_store_paths:
        assert run_command(["git", "check-ignore", "--no-index", path], cwd=target, check=False).returncode == 0

    old_rules = gitignore_file.read_text().replace(ignore_entry + "\n", "")
    gitignore_file.write_text(".DS_Store\n" + old_rules)
    records = patches_file.read_text().split("[[applied]]")
    patches_file.write_text("[[applied]]".join(record for record in records if patch_id not in record))
    assert run_command(["git", "check-ignore", "--no-index", ds_store_paths[0]], cwd=target, check=False).returncode == 1

    result = run_command([sys.executable, "-B", str(HARNESS_ROOT / "setup.py"), "--update"], cwd=target)

    assert "ignored .DS_Store files throughout .agent_core/" in result.stdout
    assert patch_id in patches_file.read_text()
    for path in ds_store_paths:
        assert run_command(["git", "check-ignore", "--no-index", path], cwd=target, check=False).returncode == 0
    for path in [".agent_core/config.toml", ".agent_core/docs/notes.md", ".agent_core/specs/example/tasks/task.md"]:
        assert run_command(["git", "check-ignore", "--no-index", path], cwd=target, check=False).returncode == 1

    updated_rules = gitignore_file.read_text()
    assert updated_rules == ".DS_Store\n" + old_rules + ignore_entry + "\n"
    run_command([sys.executable, "-B", str(HARNESS_ROOT / "setup.py"), "--update"], cwd=target)
    assert gitignore_file.read_text() == updated_rules
