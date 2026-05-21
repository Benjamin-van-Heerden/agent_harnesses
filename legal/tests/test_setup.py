import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any


LEGAL_ROOT = Path(__file__).resolve().parents[1]


def run_command(
    args: list[str],
    cwd: Path,
    check: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


def run_setup(target: Path, update: bool = False) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, "-B", str(LEGAL_ROOT / "setup.py")]
    if update:
        args.append("--update")
    return run_command(args, cwd=target)


def read_toml(path: Path) -> dict[str, Any]:
    with open(path, "rb") as file:
        data = tomllib.load(file)
    return data if isinstance(data, dict) else {}


def test_setup_installs_native_harness_and_preserves_user_content(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    (target / "AGENTS.md").write_text("Existing lawyer-specific instruction.\n")

    result = run_setup(target)

    assert result.returncode == 0
    assert (target / ".agent_core" / "harness" / "main.py").is_file()
    assert (target / ".agent_core" / "practice" / "lawyer_profile.md").is_file()
    assert (target / ".agent_core" / "docs" / "legal_context.typ").is_file()
    assert (target / ".agent_core" / "docs" / "typst_basic_reference.typ").read_text() == (
        LEGAL_ROOT / "agent_rules" / "docs" / "core" / "typst_basic_reference.typ"
    ).read_text()
    assert (target / "src" / "types" / "Client.typ").read_text() == (LEGAL_ROOT / "src" / "types" / "Client.typ").read_text()
    assert (target / "clients").is_dir()
    assert (target / "functions").is_dir()
    assert (target / "templates").is_dir()
    assert "Existing lawyer-specific instruction." in (target / "AGENTS.md").read_text()
    assert (target / "CLAUDE.md").exists()
    assert "legal Agent Core setup" in (target / ".gitignore").read_text()

    config = read_toml(target / ".agent_core" / "config.toml")
    assert config["harness"]["name"] == "legal"
    assert "last_updated_at" in config["harness"]


def test_setup_update_refreshes_managed_runtime_without_clobbering_lawyer_state(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    profile = target / ".agent_core" / "practice" / "lawyer_profile.md"
    legal_context = target / ".agent_core" / "docs" / "legal_context.typ"
    custom_source = target / "src" / "functions" / "custom.typ"
    custom_template = target / ".agent_core" / "practice" / "templates" / "custom.md"
    client_note = target / "clients" / "smith" / "profile.md"
    stale_harness_file = target / ".agent_core" / "harness" / "stale.txt"

    profile.write_text("lawyer profile edited by lawyer\n")
    legal_context.write_text("legal context edited by lawyer\n")
    custom_source.parent.mkdir(parents=True, exist_ok=True)
    custom_source.write_text("#let custom = true\n")
    custom_template.write_text("custom skeleton\n")
    client_note.parent.mkdir(parents=True, exist_ok=True)
    client_note.write_text("confidential client state\n")
    stale_harness_file.write_text("stale runtime\n")
    (target / ".agent_core" / "docs" / "typst_basic_reference.typ").write_text("stale managed doc\n")
    (target / "src" / "types" / "Client.typ").write_text("stale managed source\n")

    result = run_setup(target, update=True)

    assert "Removed stale managed file: .agent_core/harness/stale.txt" in result.stdout
    assert profile.read_text() == "lawyer profile edited by lawyer\n"
    assert legal_context.read_text() == "legal context edited by lawyer\n"
    assert custom_source.read_text() == "#let custom = true\n"
    assert custom_template.read_text() == "custom skeleton\n"
    assert client_note.read_text() == "confidential client state\n"
    assert not stale_harness_file.exists()
    assert (target / ".agent_core" / "docs" / "typst_basic_reference.typ").read_text() == (
        LEGAL_ROOT / "agent_rules" / "docs" / "core" / "typst_basic_reference.typ"
    ).read_text()
    assert (target / "src" / "types" / "Client.typ").read_text() == (LEGAL_ROOT / "src" / "types" / "Client.typ").read_text()


def test_setup_update_migrates_legacy_agent_rules_state(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    legacy = target / "agent_rules"
    matter = target / "clients" / "smith" / "matters" / "open" / "20260521-litigation-dispute"
    matter_info = matter / "info"

    (legacy / "docs" / "core").mkdir(parents=True)
    (legacy / "memories").mkdir(parents=True)
    (legacy / "log").mkdir(parents=True)
    (legacy / "todos" / "claimed").mkdir(parents=True)
    (legacy / "skeletons").mkdir(parents=True)
    matter_info.mkdir(parents=True)

    (legacy / "lawyer_profile.md").write_text("legacy lawyer profile\n")
    (legacy / "docs" / "core" / "legal_context.typ").write_text("legacy legal context\n")
    (legacy / "memories" / "drafting.md").write_text("legacy memory\n")
    (legacy / "log" / "session.md").write_text("legacy log\n")
    (legacy / "skeletons" / "status.md").write_text("legacy skeleton\n")
    (matter_info / "status.md").write_text("matter status\n")
    (legacy / "todos" / "practice.md").write_text("---\nmatter: null\n---\npractice todo\n")
    (legacy / "todos" / "matter.md").write_text(
        "---\nmatter: clients/smith/matters/open/20260521-litigation-dispute\n---\nmatter todo\n"
    )
    (legacy / "todos" / "claimed" / "done.md").write_text(
        "---\nmatter: clients/smith/matters/open/20260521-litigation-dispute\n---\ndone todo\n"
    )

    run_setup(target, update=True)

    assert (target / ".agent_core" / "practice" / "lawyer_profile.md").read_text() == "legacy lawyer profile\n"
    assert (target / ".agent_core" / "docs" / "legal_context.typ").read_text() == "legacy legal context\n"
    assert (target / ".agent_core" / "practice" / "memories" / "drafting.md").read_text() == "legacy memory\n"
    assert (target / ".agent_core" / "practice" / "logs" / "session.md").read_text() == "legacy log\n"
    assert (target / ".agent_core" / "practice" / "templates" / "status.md").read_text() == "legacy skeleton\n"
    assert (target / ".agent_core" / "practice" / "todos" / "open" / "practice.md").read_text().endswith("practice todo\n")
    assert (matter / "info" / "todos" / "matter.md").read_text().endswith("matter todo\n")
    assert (matter / "info" / "todos" / "claimed" / "done.md").read_text().endswith("done todo\n")


def test_installed_onboard_command_runs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    result = run_command([sys.executable, "-B", ".agent_core/harness/main.py", "onboard"], cwd=target)

    assert result.returncode == 0
    assert "Legal onboard context" in result.stdout
    assert "You must read the relevant profile" in result.stdout


def test_installed_runtime_foundation_commands_run(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    help_result = run_command([sys.executable, "-B", ".agent_core/harness/main.py", "--help"], cwd=target)
    assert "client" in help_result.stdout
    assert "matter" in help_result.stdout
    assert "obligation" in help_result.stdout
    assert "lint" in help_result.stdout

    paths_result = run_command([sys.executable, "-B", ".agent_core/harness/main.py", "paths"], cwd=target)
    assert f"Project root: {target}" in paths_result.stdout
    assert f"Practice root: {target / '.agent_core' / 'practice'}" in paths_result.stdout

    config_result = run_command([sys.executable, "-B", ".agent_core/harness/main.py", "config", "show"], cwd=target)
    assert "Harness: legal" in config_result.stdout
    assert "Local git snapshots: True" in config_result.stdout


def test_markdown_frontmatter_utilities_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "status.md"
    script = f"""
from pathlib import Path
from src.utils.markdown import MarkdownDocument, frontmatter_get, frontmatter_set, read_markdown, write_markdown

path = Path({str(path)!r})
write_markdown(path, MarkdownDocument(frontmatter={{"status": "open", "priority": "high"}}, body="Matter body\\n"))
assert frontmatter_get(path, "status") == "open"
assert read_markdown(path).body == "Matter body\\n"
frontmatter_set(path, "status", "resolved")
document = read_markdown(path)
assert document.frontmatter["status"] == "resolved"
assert document.frontmatter["priority"] == "high"
assert document.body == "Matter body\\n"
""".strip()

    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=tmp_path,
        extra_env={"PYTHONPATH": str(LEGAL_ROOT / ".agent_core" / "harness")},
    )


def test_state_models_and_helpers_create_legacy_compatible_records(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from pathlib import Path

from src.state.clients import create_client, list_clients
from src.state.communications import log_communication, record_note
from src.state.deadlines import add_deadline, read_deadlines, upcoming_deadlines
from src.state.logs import create_work_log, recent_work_logs
from src.state.matters import close_matter, create_matter, list_open_matters, resolve_matter
from src.state.memories import create_memory, list_memories
from src.state.obligations import create_obligation
from src.state.todos import claim_todo, create_todo, list_matter_todos, list_practice_todos
from src.utils.markdown import frontmatter_get

client_profile = create_client("smith", "Smith Corp", "company")
assert client_profile == Path("clients/smith/profile.md").resolve()
assert list_clients()[0].display_name == "Smith Corp"

matter_dir = create_matter("smith", "litigation", "jones_dispute", "high", "hourly")
assert (matter_dir / "info/status.md").is_file()
assert (matter_dir / "info/chronology").is_dir()
assert (matter_dir / "info/obligations").is_dir()
assert (matter_dir / "info/todos").is_dir()
assert list_open_matters()[0].priority == "high"
assert resolve_matter("jones_dispute") == matter_dir

deadline_file = add_deadline("jones_dispute", "2999-05-21", "filing", "Answering affidavit")
assert read_deadlines(deadline_file)[0].description == "Answering affidavit"
assert frontmatter_get(matter_dir / "info/status.md", "next_deadline") == "2999-05-21"
assert upcoming_deadlines(400000)[0][2].category == "filing"

record_file = log_communication("jones_dispute", "2026-05-21", "in", "email", "Jones", "Settlement proposal")
record_note("jones_dispute", "2026-05-21", "Internal note\\nLonger body")
record_text = record_file.read_text()
assert "comm:in:email" in record_text
assert "Jones — Settlement proposal" in record_text
assert "Internal note" in record_text

practice_todo = create_todo("review_rules", "Review court rules", "normal")
matter_todo = create_todo("draft_affidavit", "Draft affidavit", "high", "jones_dispute")
assert list_practice_todos()[0].path == practice_todo
assert list_matter_todos("jones_dispute")[0].path == matter_todo
claimed = claim_todo("draft_affidavit", "jones_dispute")
assert claimed.name == "draft_affidavit.md"
assert "status: claimed" in claimed.read_text()

memory = create_memory("affidavit_style", "Affidavit style")
assert list_memories()[0].path == memory

work_log = create_work_log("jones_dispute")
assert recent_work_logs()[0].path == work_log

obligation = create_obligation("jones_dispute", "prepare_bundle", "preparation", "2999-05-20", "Prepare indexed bundle")
assert 'category = "preparation"' in obligation.read_text()

resolved = close_matter("jones_dispute")
assert resolved.parent.name == "resolved"
assert (resolved / "info/status.md").is_file()
""".strip()

    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".agent_core" / "harness")},
    )


def test_context_commands_report_installed_legal_state(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from pathlib import Path

from src.state.clients import create_client
from src.state.deadlines import add_deadline
from src.state.matters import create_matter
from src.state.memories import create_memory
from src.state.todos import create_todo

create_client("smith", "Smith Corp", "company")
matter_dir = create_matter("smith", "litigation", "jones_dispute", "urgent", "hourly")
add_deadline("jones_dispute", "2999-05-21", "filing", "Answering affidavit")
create_todo("practice_review", "Review practice note", "normal")
create_todo("draft_affidavit", "Draft affidavit", "high", "jones_dispute")
create_memory("drafting_style", "Drafting style")
(matter_dir / "raw" / "brief.pdf").write_text("raw")
""".strip()
    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".agent_core" / "harness")},
    )

    harness = [sys.executable, "-B", ".agent_core/harness/main.py"]

    onboard = run_command([*harness, "onboard"], cwd=target)
    assert "Legal onboard context" in onboard.stdout
    assert "Clients: 1" in onboard.stdout
    assert "Open matters: 1" in onboard.stdout
    assert "High-priority matters:" in onboard.stdout

    clients = run_command([*harness, "client", "list"], cwd=target)
    assert "smith\tSmith Corp\tcompany\t1\t0" in clients.stdout

    matters = run_command([*harness, "matter", "list"], cwd=target)
    assert "smith\t" in matters.stdout
    assert "urgent" in matters.stdout
    assert "draft_affidavit" not in matters.stdout

    found = run_command([*harness, "matter", "find", "jones"], cwd=target)
    assert "clients/smith/matters/open/" in found.stdout

    focus = run_command([*harness, "matter", "focus", "jones"], cwd=target)
    assert "Focused matter:" in focus.stdout
    assert "Unparsed raw files: 1" in focus.stdout
    assert "Draft affidavit" in focus.stdout

    unparsed = run_command([*harness, "matter", "list-unparsed", "jones"], cwd=target)
    assert "brief.pdf" in unparsed.stdout

    deadlines = run_command([*harness, "deadline", "upcoming", "400000"], cwd=target)
    assert "2999-05-21" in deadlines.stdout
    assert "Answering affidavit" in deadlines.stdout

    todos = run_command([*harness, "todo", "list"], cwd=target)
    assert "practice_review\tnormal\tReview practice note" in todos.stdout

    matter_todos = run_command([*harness, "todo", "list", "jones"], cwd=target)
    assert "draft_affidavit\thigh\tDraft affidavit" in matter_todos.stdout

    lint = run_command([*harness, "lint"], cwd=target)
    assert "all frontmatter valid" in lint.stdout
