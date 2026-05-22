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
    assert (target / ".agent_core" / "docs" / "legal_harness_function.md").is_file()
    assert (target / ".agent_core" / "docs" / "legal_harness_typst_basic_reference.typ").read_text() == (
        LEGAL_ROOT / "optional_docs" / "legal_harness_typst_basic_reference.typ"
    ).read_text()
    assert (target / ".agent_core" / "docs" / "legal_harness_typst_soft_typesystem_and_house_rules.typ").read_text() == (
        LEGAL_ROOT / "optional_docs" / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).read_text()
    assert not (target / ".agent_core" / "docs" / "typst_basic_reference.typ").exists()
    assert not (target / ".agent_core" / "docs" / "typst_soft_typesystem_and_house_rules_updated.typ").exists()
    assert not (target / ".agent_core" / "docs" / "typst_detailed_reference.typ").exists()
    assert (target / ".agent_docs" / "typst_detailed_reference.typ").read_text() == (
        LEGAL_ROOT / ".agent_docs" / "typst_detailed_reference.typ"
    ).read_text()
    assert (target / "src" / "types" / "Client.typ").read_text() == (LEGAL_ROOT / "src" / "types" / "Client.typ").read_text()
    assert (target / "clients").is_dir()
    assert (target / "functions").is_dir()
    assert (target / "templates").is_dir()
    agents_text = (target / "AGENTS.md").read_text()
    assert "Existing lawyer-specific instruction." in agents_text
    assert "python -B .agent_core/harness/main.py onboard" in agents_text
    assert "agent_rules/commands" not in agents_text
    assert "agent_rules/scripts" not in agents_text
    assert (target / "CLAUDE.md").exists()
    assert "legal Agent Core setup" in (target / ".gitignore").read_text()
    assert (LEGAL_ROOT / "README.md").is_file()
    assert not (LEGAL_ROOT / "agent_rules").exists()
    assert not (LEGAL_ROOT / "bash_setup.sh").exists()

    config = read_toml(target / ".agent_core" / "config.toml")
    assert config["harness"]["name"] == "legal"
    assert config["harness"]["update_interval_days"] == 3
    assert "last_updated_at" in config["harness"]
    assert (target / ".agent_core" / "harness" / "update.py").is_file()


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
    (target / ".agent_core" / "docs" / "legal_harness_typst_basic_reference.typ").write_text("stale managed doc\n")
    (target / ".agent_core" / "docs" / "legal_harness_typst_soft_typesystem_and_house_rules.typ").write_text("stale soft type doc\n")
    (target / ".agent_core" / "docs" / "typst_basic_reference.typ").write_text("old managed doc\n")
    (target / ".agent_core" / "docs" / "typst_soft_typesystem_and_house_rules_updated.typ").write_text("old soft type doc\n")
    (target / ".agent_docs" / "typst_detailed_reference.typ").write_text("stale detailed doc\n")
    (target / "src" / "types" / "Client.typ").write_text("stale managed source\n")

    result = run_setup(target, update=True)

    assert "Removed stale managed file: .agent_core/harness/stale.txt" in result.stdout
    assert profile.read_text() == "lawyer profile edited by lawyer\n"
    assert legal_context.read_text() == "legal context edited by lawyer\n"
    assert custom_source.read_text() == "#let custom = true\n"
    assert custom_template.read_text() == "custom skeleton\n"
    assert client_note.read_text() == "confidential client state\n"
    assert not stale_harness_file.exists()
    assert "Updated optional doc: legal_harness_typst_basic_reference" in result.stdout
    assert "Removed renamed managed doc: .agent_core/docs/typst_basic_reference.typ" in result.stdout
    assert (target / ".agent_core" / "docs" / "legal_harness_typst_basic_reference.typ").read_text() == (
        LEGAL_ROOT / "optional_docs" / "legal_harness_typst_basic_reference.typ"
    ).read_text()
    assert (target / ".agent_core" / "docs" / "legal_harness_typst_soft_typesystem_and_house_rules.typ").read_text() == (
        LEGAL_ROOT / "optional_docs" / "legal_harness_typst_soft_typesystem_and_house_rules.typ"
    ).read_text()
    assert not (target / ".agent_core" / "docs" / "typst_basic_reference.typ").exists()
    assert not (target / ".agent_core" / "docs" / "typst_soft_typesystem_and_house_rules_updated.typ").exists()
    assert (target / ".agent_docs" / "typst_detailed_reference.typ").read_text() == (
        LEGAL_ROOT / ".agent_docs" / "typst_detailed_reference.typ"
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
    (legacy / "todos" / "global.md").write_text("---\nmatter: null\n---\nglobal todo\n")
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
    assert (target / ".agent_core" / "todos" / "open" / "global.md").read_text().endswith("global todo\n")
    assert (matter / "info" / "todos" / "matter.md").read_text().endswith("matter todo\n")
    assert (matter / "info" / "todos" / "claimed" / "done.md").read_text().endswith("done todo\n")


def test_installed_onboard_command_runs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    result = run_command([sys.executable, "-B", ".agent_core/harness/main.py", "onboard"], cwd=target)

    assert result.returncode == 0
    assert "Legal onboard context" in result.stdout
    assert "Required docs" in result.stdout
    assert "# .agent_core/docs/legal_harness_function.md" in result.stdout
    assert "# .agent_core/docs/legal_context.typ" in result.stdout
    assert "You must read the relevant profile" in result.stdout


def test_setup_docs_commands_manage_optional_docs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    docs_list = run_command([sys.executable, "-B", str(LEGAL_ROOT / "setup.py"), "docs", "list"], cwd=target)
    assert "legal_harness_function" in docs_list.stdout
    assert "legal_harness_typst_basic_reference" in docs_list.stdout

    target_doc = target / ".agent_core" / "docs" / "legal_harness_typst_basic_reference.typ"
    target_doc.unlink()
    docs_add = run_command(
        [sys.executable, "-B", str(LEGAL_ROOT / "setup.py"), "docs", "add", "legal_harness_typst_basic_reference"],
        cwd=target,
    )
    assert "Added optional doc: legal_harness_typst_basic_reference" in docs_add.stdout
    assert target_doc.is_file()

    target_doc.write_text("stale\n")
    docs_update = run_command([sys.executable, "-B", str(LEGAL_ROOT / "setup.py"), "docs", "update"], cwd=target)
    assert "Updated optional doc: legal_harness_typst_basic_reference" in docs_update.stdout
    assert target_doc.read_text() == (LEGAL_ROOT / "optional_docs" / "legal_harness_typst_basic_reference.typ").read_text()


def test_installed_runtime_foundation_commands_run(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    help_result = run_command([sys.executable, "-B", ".agent_core/harness/main.py", "--help"], cwd=target)
    assert "client" in help_result.stdout
    assert "matter" in help_result.stdout
    assert "chronology" in help_result.stdout
    assert "obligation" in help_result.stdout
    assert "deadline" not in help_result.stdout
    assert "record" not in help_result.stdout
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


def test_state_models_and_helpers_create_native_records(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from pathlib import Path

from src.state.clients import create_client, list_clients
from src.state.chronology import add_chronology_event, list_chronology
from src.state.logs import create_work_log, recent_work_logs
from src.state.matters import close_matter, create_matter, list_open_matters, resolve_matter
from src.state.memories import create_memory, list_memories
from src.state.obligations import create_obligation, upcoming_obligations
from src.state.todos import claim_todo, create_todo, list_global_todos, list_matter_todos
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

deadline_file = create_obligation("jones_dispute", "answering_affidavit", "deadline", "2999-05-21", "filing — Answering affidavit")
assert deadline_file.parent.name == "deadline"
assert 'kind = "deadline"' in deadline_file.read_text()
assert 'description = "filing — Answering affidavit"' in deadline_file.read_text()
assert frontmatter_get(matter_dir / "info/status.md", "next_obligation") == "2999-05-21"
assert upcoming_obligations(400000)[0][2].kind == "deadline"

add_chronology_event("jones_dispute", "2026-05-21", "email", "in: Jones — Settlement proposal", "_TODO: body_")
add_chronology_event("jones_dispute", "2026-05-21", "note", "Internal note", "Longer body")
chronology = list_chronology("jones_dispute")
assert any(entry.kind == "email" and "Jones" in entry.summary for entry in chronology)
assert any(entry.kind == "note" and entry.summary == "Internal note" for entry in chronology)
assert len(list((matter_dir / "info" / "chronology").glob("*/*.toml"))) >= 3

global_todo = create_todo("review_rules", "Review court rules", "normal")
matter_todo = create_todo("draft_affidavit", "Draft affidavit", "high", "jones_dispute")
assert list_global_todos()[0].path == global_todo
assert list_matter_todos("jones_dispute")[0].path == matter_todo
claimed = claim_todo("draft_affidavit", "jones_dispute")
assert claimed.name == "draft_affidavit.md"
assert "status: claimed" in claimed.read_text()

memory = create_memory("affidavit_style", "Affidavit style")
assert list_memories()[0].path == memory

work_log = create_work_log("jones_dispute")
assert recent_work_logs()[0].path == work_log

obligation = create_obligation("jones_dispute", "prepare_bundle", "preparation", "2999-05-20", "Prepare indexed bundle")
assert 'kind = "preparation"' in obligation.read_text()

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
from src.state.matters import create_matter
from src.state.memories import create_memory
from src.state.obligations import create_obligation
from src.state.todos import create_todo

create_client("smith", "Smith Corp", "company")
matter_dir = create_matter("smith", "litigation", "jones_dispute", "urgent", "hourly")
create_obligation("jones_dispute", "answering_affidavit", "deadline", "2999-05-21", "filing — Answering affidavit")
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
    assert "Practice summary" in onboard.stdout
    assert "Clients" in onboard.stdout
    assert "Open matters" in onboard.stdout
    assert "✅ Todos" in onboard.stdout
    assert "Review practice note" in onboard.stdout
    assert "Global" in onboard.stdout
    assert "Draft affidavit" in onboard.stdout
    assert "clients/smith/matters/open/" in onboard.stdout
    assert "High-priority matters" in onboard.stdout

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
    assert "Matter focus read set:" in focus.stdout
    assert "Unparsed raw files: 1" in focus.stdout
    assert "Draft affidavit" in focus.stdout
    assert "You must read status, relevant chronology" not in focus.stdout

    unparsed = run_command([*harness, "matter", "list-unparsed", "jones"], cwd=target)
    assert "brief.pdf" in unparsed.stdout

    obligations = run_command([*harness, "obligation", "list", "jones"], cwd=target)
    assert "2999-05-21" in obligations.stdout
    assert "Answering affidavit" in obligations.stdout

    todos = run_command([*harness, "todo", "list"], cwd=target)
    assert "practice_review\tnormal\tReview practice note" in todos.stdout

    matter_todos = run_command([*harness, "todo", "list", "jones"], cwd=target)
    assert "draft_affidavit\thigh\tDraft affidavit" in matter_todos.stdout

    lint = run_command([*harness, "lint"], cwd=target)
    assert "all frontmatter valid" in lint.stdout


def test_onboard_creates_session_log_and_removes_untouched_empty_logs(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = [sys.executable, "-B", ".agent_core/harness/main.py"]
    first = run_command([*harness, "onboard"], cwd=target)
    assert "Session work log" in first.stdout
    assert "✅ Todos" not in first.stdout
    assert "surfaced todos" not in first.stdout
    logs_root = target / ".agent_core" / "practice" / "logs"
    first_logs = sorted(logs_root.glob("*.md"))
    assert len(first_logs) == 1
    assert "## What was done\n_TODO_" in first_logs[0].read_text()

    second = run_command([*harness, "onboard"], cwd=target)
    assert "Removed empty work logs: 1" in second.stdout
    second_logs = sorted(logs_root.glob("*.md"))
    assert len(second_logs) == 1

    edited = second_logs[0]
    edited.write_text(edited.read_text().replace("## What was done\n_TODO_", "## What was done\nOpened the file and reviewed context."))
    third = run_command([*harness, "onboard"], cwd=target)
    assert "Removed empty work logs" not in third.stdout
    assert len(sorted(logs_root.glob("*.md"))) == 2


def test_lifecycle_commands_create_and_resolve_chronology(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = [sys.executable, "-B", ".agent_core/harness/main.py"]

    client = run_command([*harness, "client", "new", "smith", "Smith Corp", "company"], cwd=target)
    assert "Created client: smith (Smith Corp)" in client.stdout
    assert "clients/smith/profile.md" in client.stdout
    assert (target / "clients" / "smith" / "profile.md").is_file()

    invalid_client = run_command([*harness, "client", "new", "Smith", "Smith Corp", "company"], cwd=target, check=False)
    assert invalid_client.returncode == 1
    assert "invalid slug 'Smith'" in invalid_client.stderr

    missing_client = run_command([*harness, "matter", "new", "missing", "litigation", "shareholder_dispute"], cwd=target, check=False)
    assert missing_client.returncode == 1
    assert "client not found: missing" in missing_client.stderr

    invalid_priority = run_command([*harness, "matter", "new", "smith", "litigation", "shareholder_dispute", "critical"], cwd=target, check=False)
    assert invalid_priority.returncode == 1
    assert "invalid priority 'critical'" in invalid_priority.stderr

    matter = run_command([*harness, "matter", "new", "smith", "litigation", "shareholder_dispute", "high", "fixed"], cwd=target)
    assert "Created matter:" in matter.stdout
    assert "shareholder_dispute" in matter.stdout
    open_matters = sorted((target / "clients" / "smith" / "matters" / "open").iterdir())
    assert len(open_matters) == 1
    matter_dir = open_matters[0]
    assert (matter_dir / "info" / "status.md").is_file()
    assert list((matter_dir / "info" / "chronology" / "matter_opened").glob("*.toml"))

    resolved = run_command([*harness, "matter", "resolve", "shareholder_dispute"], cwd=target)
    assert "Resolved matter:" in resolved.stdout
    resolved_dir = target / "clients" / "smith" / "matters" / "resolved" / matter_dir.name
    assert resolved_dir.is_dir()
    assert not matter_dir.exists()
    assert "status: resolved" in (resolved_dir / "info" / "status.md").read_text()
    assert list((resolved_dir / "info" / "chronology" / "matter_resolved").glob("*.toml"))

    clients = run_command([*harness, "client", "list"], cwd=target)
    assert "smith\tSmith Corp\tcompany\t0\t1" in clients.stdout


def test_bookkeeping_commands_create_chronology_obligations_and_todos(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = [sys.executable, "-B", ".agent_core/harness/main.py"]
    run_command([*harness, "client", "new", "smith", "Smith Corp", "company"], cwd=target)
    run_command([*harness, "matter", "new", "smith", "litigation", "shareholder_dispute", "high", "hourly"], cwd=target)
    matter_dir = next((target / "clients" / "smith" / "matters" / "open").iterdir())

    deadline = run_command([*harness, "obligation", "add", "deadline", "shareholder_dispute", "answering_affidavit", "2999-05-21", "filing — Answering affidavit"], cwd=target)
    assert "Added obligation: deadline due 2999-05-21" in deadline.stdout
    obligations = list((matter_dir / "info" / "obligations" / "deadline").glob("*.toml"))
    assert len(obligations) == 1
    assert 'kind = "deadline"' in obligations[0].read_text()
    assert 'description = "filing — Answering affidavit"' in obligations[0].read_text()
    status_text = (matter_dir / "info" / "status.md").read_text()
    assert "next_obligation:" in status_text
    assert "2999-05-21" in status_text

    invalid_deadline = run_command([*harness, "obligation", "add", "deadline", "shareholder_dispute", "bad_date", "21-05-2999", "Bad date"], cwd=target, check=False)
    assert invalid_deadline.returncode == 1
    assert "date must be YYYY-MM-DD" in invalid_deadline.stderr

    communication = run_command([*harness, "chronology", "add", "email", "shareholder_dispute", "2026-05-21", "in", "Jones", "Settlement proposal"], cwd=target)
    assert "Added chronology event: email" in communication.stdout

    invalid_direction = run_command([*harness, "chronology", "add", "email", "shareholder_dispute", "2026-05-21", "sideways", "Jones", "Bad direction"], cwd=target, check=False)
    assert invalid_direction.returncode == 1
    assert "direction must be 'in' or 'out'" in invalid_direction.stderr

    note = run_command([*harness, "chronology", "add", "note", "shareholder_dispute", "2026-05-21", "Internal note", "Longer body"], cwd=target)
    assert "Added chronology event: note" in note.stdout
    chronology_files = list((matter_dir / "info" / "chronology").glob("*/*.toml"))
    assert any('kind = "email"' in path.read_text() and "Jones" in path.read_text() for path in chronology_files)
    assert any('kind = "note"' in path.read_text() for path in chronology_files)

    global_todo = run_command([*harness, "todo", "new", "review_rules", "Review court rules", "normal"], cwd=target)
    assert "Created global todo: review_rules" in global_todo.stdout
    global_todo_file = target / ".agent_core" / "todos" / "open" / "review_rules.md"
    assert global_todo_file.is_file()

    matter_todo = run_command([*harness, "todo", "new", "draft_affidavit", "Draft affidavit", "high", "shareholder_dispute"], cwd=target)
    assert "Created matter todo: draft_affidavit" in matter_todo.stdout
    matter_todo_file = matter_dir / "info" / "todos" / "draft_affidavit.md"
    assert matter_todo_file.is_file()

    invalid_todo = run_command([*harness, "todo", "new", "bad_priority", "Bad priority", "urgent"], cwd=target, check=False)
    assert invalid_todo.returncode == 1
    assert "invalid priority 'urgent'" in invalid_todo.stderr

    claimed = run_command([*harness, "todo", "claim", "draft_affidavit", "shareholder_dispute"], cwd=target)
    assert "Claimed todo: draft_affidavit" in claimed.stdout
    assert not matter_todo_file.exists()
    claimed_file = matter_dir / "info" / "todos" / "claimed" / "draft_affidavit.md"
    assert claimed_file.is_file()
    assert "status: claimed" in claimed_file.read_text()

    memory = run_command([*harness, "memory", "new", "affidavit_style", "Affidavit style"], cwd=target)
    assert "Created memory: affidavit_style" in memory.stdout
    memory_file = target / ".agent_core" / "practice" / "memories" / "affidavit_style.md"
    assert memory_file.is_file()
    assert "_TODO_" in memory_file.read_text()

    work_log = run_command([*harness, "log", "new", "shareholder_dispute"], cwd=target)
    assert "Created work log:" in work_log.stdout
    assert "replace every TODO" in work_log.stdout
    log_files = list((target / ".agent_core" / "practice" / "logs").glob("*.md"))
    assert len(log_files) == 1
    assert "matter: clients/smith/matters/open/" in log_files[0].read_text()

    obligation = run_command([*harness, "obligation", "list", "shareholder_dispute"], cwd=target)
    assert "deadline\topen\tfiling — Answering affidavit" in obligation.stdout
