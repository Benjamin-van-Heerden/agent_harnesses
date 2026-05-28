import sys
from pathlib import Path

from helpers import LEGAL_ROOT, run_command, run_setup


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
assert client_profile == Path("ZZ_CLIENTS/SMITH/profile.md").resolve()
assert list_clients()[0].display_name == "Smith Corp"

matter_dir = create_matter("smith", "litigation", "jones_dispute", "high", "hourly")
assert (matter_dir / "info/status.md").is_file()
assert (matter_dir / "info/chronology.toml").is_file()
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
chronology_text = (matter_dir / "info" / "chronology.toml").read_text()
assert chronology_text.count("[[events]]") == 2
assert 'kind = "email"' in chronology_text
assert 'kind = "note"' in chronology_text

global_todo = create_todo("review_rules", "Review court rules", "normal")
matter_todo = create_todo("draft_affidavit", "Draft affidavit", "high", "jones_dispute")
assert list_global_todos()[0].path == global_todo
assert list_matter_todos("jones_dispute")[0].path == matter_todo
claimed = claim_todo("draft_affidavit", "jones_dispute")
assert claimed.name == "draft_affidavit.md"
assert "status: claimed" in claimed.read_text()

memory = create_memory("affidavit_style", "Affidavit style")
assert list_memories()[0].path == memory

work_log = create_work_log()
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
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )
