import sys
from pathlib import Path

from helpers import harness_command, onboard_content, run_command, run_setup


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
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )

    harness = harness_command()

    onboard = run_command([*harness, "onboard"], cwd=target)
    onboard_text = onboard_content(onboard, target)
    assert "Legal onboard context" in onboard_text
    assert "Practice summary" in onboard_text
    assert "Clients" in onboard_text
    assert "Open matters" in onboard_text
    assert "\nTodos\n-----" in onboard_text
    assert "Review practice note" in onboard_text
    assert "Global" in onboard_text
    assert "Draft affidavit" in onboard_text
    assert "ZZ_CLIENTS/SMITH/matters/open/" in onboard_text
    assert "High-priority matters" in onboard_text

    clients = run_command([*harness, "client", "list"], cwd=target)
    assert "smith\tSmith Corp\tcompany\t1\t0" in clients.stdout

    matters = run_command([*harness, "matter", "list"], cwd=target)
    assert "smith\t" in matters.stdout
    assert "urgent" in matters.stdout
    assert "draft_affidavit" not in matters.stdout

    found = run_command([*harness, "matter", "find", "jones"], cwd=target)
    assert "ZZ_CLIENTS/SMITH/matters/open/" in found.stdout

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


def test_matter_lookup_uses_physical_files_and_metadata_and_reports_ambiguity(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from src.state.clients import create_client
from src.state.matters import create_matter, parse_matter_status
from src.utils.markdown import MarkdownDocument, read_markdown, write_markdown

create_client("smith", "Smith Corp", "entity")
first = create_matter("smith", "litigation", "lease_dispute", "high", "hourly")
first_status = first / "info" / "status.md"
first_doc = read_markdown(first_status)
first_frontmatter = dict(first_doc.frontmatter)
first_frontmatter["case_number"] = "2026/123"
first_frontmatter["physical_files"] = ["A123/24", "LIT-0042"]
first_frontmatter["workflow"] = "litigation_flow"
first_frontmatter["tags"] = ["urgent", "lease"]
write_markdown(first_status, MarkdownDocument(frontmatter=first_frontmatter, body=first_doc.body))

create_client("jones", "Jones Holdings", "entity")
second = create_matter("jones", "litigation", "lease_dispute", "normal", "hourly")
second_status = second / "info" / "status.md"
second_doc = read_markdown(second_status)
second_frontmatter = dict(second_doc.frontmatter)
second_frontmatter["physical_files"] = ["A123/24"]
write_markdown(second_status, MarkdownDocument(frontmatter=second_frontmatter, body=second_doc.body))

parsed = parse_matter_status(first_status)
assert parsed.case_number == "2026/123"
assert parsed.physical_files == ["A123/24", "LIT-0042"]
assert parsed.workflow == "litigation_flow"
assert parsed.last_touched_at is None
assert parsed.tags == ["urgent", "lease"]
""".strip()
    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )

    harness = harness_command()
    by_file = run_command([*harness, "matter", "find", "LIT-0042"], cwd=target)
    assert "ZZ_CLIENTS/SMITH/matters/open/" in by_file.stdout
    assert "ZZ_CLIENTS/JONES/matters/open/" not in by_file.stdout

    by_workflow = run_command(
        [*harness, "matter", "find", "litigation_flow"], cwd=target
    )
    assert "ZZ_CLIENTS/SMITH/matters/open/" in by_workflow.stdout

    by_client_display = run_command(
        [*harness, "matter", "find", "Jones Holdings"], cwd=target
    )
    assert "ZZ_CLIENTS/JONES/matters/open/" in by_client_display.stdout

    focus = run_command([*harness, "matter", "focus", "LIT-0042"], cwd=target)
    assert "Focused matter: ZZ_CLIENTS/SMITH/matters/open/" in focus.stdout

    ambiguous = run_command(
        [*harness, "matter", "focus", "A123/24"], cwd=target, check=False
    )
    assert ambiguous.returncode == 1
    assert "multiple matters match 'A123/24'" in ambiguous.stderr
    assert "Ask the lawyer which matter to use" in ambiguous.stderr
    assert "ZZ_CLIENTS/SMITH/matters/open/" in ambiguous.stderr
    assert "ZZ_CLIENTS/JONES/matters/open/" in ambiguous.stderr


def test_matter_touch_tracking_and_client_index(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    script = """
from src.state.clients import create_client
from src.state.matters import create_matter, parse_matter_status

create_client("smith", "Smith Corp", "entity")
matter = create_matter("smith", "litigation", "touch_test", "normal", "hourly")
assert parse_matter_status(matter / "info" / "status.md").last_touched_at is None
""".strip()
    run_command(
        [sys.executable, "-B", "-c", script],
        cwd=target,
        extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
    )

    harness = harness_command()
    matter_dir = next((target / "ZZ_CLIENTS" / "SMITH" / "matters" / "open").iterdir())
    status_file = matter_dir / "info" / "status.md"

    def touched_at() -> str:
        script_inner = f"""
from pathlib import Path
from src.state.matters import parse_matter_status

print(parse_matter_status(Path({str(status_file)!r})).last_touched_at or "")
""".strip()
        result = run_command(
            [sys.executable, "-B", "-c", script_inner],
            cwd=target,
            extra_env={"PYTHONPATH": str(target / ".praxis" / "harness")},
        )
        return result.stdout.strip()

    run_command([*harness, "matter", "find", "touch_test"], cwd=target)
    assert touched_at() == ""

    focus = run_command([*harness, "matter", "focus", "touch_test"], cwd=target)
    assert "Focused matter:" in focus.stdout
    first_touch = touched_at()
    assert first_touch

    run_command([*harness, "matter", "list"], cwd=target)
    assert touched_at() == first_touch

    run_command(
        [*harness, "todo", "new", "draft_note", "Draft note", "normal", "touch_test"],
        cwd=target,
    )
    assert touched_at() >= first_touch

    onboard = run_command([*harness, "onboard"], cwd=target)
    onboard_text = onboard_content(onboard, target)
    assert "Client matter index" in onboard_text
    assert "Smith Corp" in onboard_text
    assert "touch_test" in onboard_text
    index_text = (target / ".praxis" / "client_matter_index.toml").read_text()
    assert "Generated by the legal harness" in index_text
    assert 'slug = "smith"' in index_text
    assert "touch_test" in index_text


def test_client_new_generates_person_slugs_and_requires_collision_suffix(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()

    person = run_command(
        [*harness, "client", "new", "Van Heerden, Benjamin"], cwd=target
    )
    assert (
        "Created client: van_heerden_benjamin (Van Heerden, Benjamin)" in person.stdout
    )
    assert (target / "ZZ_CLIENTS" / "VAN_HEERDEN_BENJAMIN" / "profile.md").is_file()

    collision = run_command(
        [*harness, "client", "new", "Van Heerden, Benjamin"], cwd=target, check=False
    )
    assert collision.returncode == 1
    assert "Ask the lawyer for a distinguishing suffix" in collision.stderr
    assert "location, ID hint, company, or role" in collision.stderr

    suffixed = run_command(
        [*harness, "client", "new", "Van Heerden, Benjamin", "--suffix", "pretoria"],
        cwd=target,
    )
    assert (
        "Created client: van_heerden_benjamin_pretoria (Van Heerden, Benjamin)"
        in suffixed.stdout
    )
    assert (
        target / "ZZ_CLIENTS" / "VAN_HEERDEN_BENJAMIN_PRETORIA" / "profile.md"
    ).is_file()

    entity = run_command(
        [*harness, "client", "new", "Acme Trading (Pty) Ltd", "entity"], cwd=target
    )
    assert (
        "Created client: acme_trading_pty_ltd (Acme Trading (Pty) Ltd)" in entity.stdout
    )
    assert (target / "ZZ_CLIENTS" / "ACME_TRADING_PTY_LTD" / "profile.md").is_file()


def test_lifecycle_commands_create_and_resolve_chronology(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()

    client = run_command(
        [*harness, "client", "new", "Smith Corp", "entity", "--slug", "smith"],
        cwd=target,
    )
    assert "Created client: smith (Smith Corp)" in client.stdout
    assert "ZZ_CLIENTS/SMITH/profile.md" in client.stdout
    assert (target / "ZZ_CLIENTS" / "SMITH" / "profile.md").is_file()

    invalid_client = run_command(
        [*harness, "client", "new", "Smith"], cwd=target, check=False
    )
    assert invalid_client.returncode == 1
    assert "natural person client names must be surname-first" in invalid_client.stderr

    missing_client = run_command(
        [*harness, "matter", "new", "missing", "litigation", "shareholder_dispute"],
        cwd=target,
        check=False,
    )
    assert missing_client.returncode == 1
    assert "client not found: missing" in missing_client.stderr

    invalid_priority = run_command(
        [
            *harness,
            "matter",
            "new",
            "smith",
            "litigation",
            "shareholder_dispute",
            "critical",
        ],
        cwd=target,
        check=False,
    )
    assert invalid_priority.returncode == 1
    assert "invalid priority 'critical'" in invalid_priority.stderr

    matter = run_command(
        [
            *harness,
            "matter",
            "new",
            "smith",
            "litigation",
            "shareholder_dispute",
            "high",
            "fixed",
        ],
        cwd=target,
    )
    assert "Created matter:" in matter.stdout
    assert "shareholder_dispute" in matter.stdout
    open_matters = sorted(
        (target / "ZZ_CLIENTS" / "SMITH" / "matters" / "open").iterdir()
    )
    assert len(open_matters) == 1
    matter_dir = open_matters[0]
    assert (matter_dir / "info" / "status.md").is_file()
    assert list((matter_dir / "info" / "chronology" / "matter_opened").glob("*.toml"))

    resolved = run_command(
        [*harness, "matter", "resolve", "shareholder_dispute"], cwd=target
    )
    assert "Resolved matter:" in resolved.stdout
    resolved_dir = (
        target / "ZZ_CLIENTS" / "SMITH" / "matters" / "resolved" / matter_dir.name
    )
    assert resolved_dir.is_dir()
    assert not matter_dir.exists()
    assert "status: resolved" in (resolved_dir / "info" / "status.md").read_text()
    assert list(
        (resolved_dir / "info" / "chronology" / "matter_resolved").glob("*.toml")
    )

    clients = run_command([*harness, "client", "list"], cwd=target)
    assert "smith\tSmith Corp\tentity\t0\t1" in clients.stdout


def test_unbound_matter_creation_onboard_and_binding(tmp_path: Path) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()
    unbound = run_command(
        [
            *harness,
            "matter",
            "new",
            "--unbound",
            "VALUATIONS/CHARL_VAN_DUYKER_VALUATIONS/Grobler Abbey Valuation",
            "--priority",
            "high",
        ],
        cwd=target,
    )
    assert "Created unbound matter: grobler_abbey_valuation" in unbound.stdout
    unbound_dir = (
        target
        / "UNBOUND"
        / "open"
        / "VALUATIONS"
        / "CHARL_VAN_DUYKER_VALUATIONS"
        / "grobler_abbey_valuation"
    )
    assert (unbound_dir / "info" / "status.md").is_file()
    assert "workspace: unbound" in (unbound_dir / "info" / "status.md").read_text()

    legacy = target / "UNBOUND" / "VALUATIONS" / "LEGACY_VALUATION"
    legacy.mkdir(parents=True)
    (legacy / "legacy.typ").write_text("#let x = 1")

    listed = run_command([*harness, "matter", "list", "--unbound"], cwd=target)
    assert "grobler_abbey_valuation" in listed.stdout
    assert "Untracked legacy unbound bundles" in listed.stdout
    assert "UNBOUND/VALUATIONS/LEGACY_VALUATION" in listed.stdout

    onboard = run_command([*harness, "onboard"], cwd=target)
    onboard_text = onboard_content(onboard, target)
    assert "Unbound matters" in onboard_text
    assert "grobler_abbey_valuation" in onboard_text
    assert "UNBOUND/VALUATIONS/LEGACY_VALUATION" in onboard_text

    run_command(
        [*harness, "client", "new", "Smith Corp", "entity", "--slug", "smith"],
        cwd=target,
    )
    bound = run_command(
        [
            *harness,
            "matter",
            "bind",
            "grobler_abbey_valuation",
            "smith",
            "valuation",
            "grobler_abbey",
            "high",
            "hourly",
        ],
        cwd=target,
    )
    assert "Bound unbound matter:" in bound.stdout
    bound_dir = next((target / "ZZ_CLIENTS" / "SMITH" / "matters" / "open").iterdir())
    status = (bound_dir / "info" / "status.md").read_text()
    assert "client: smith" in status
    assert (
        "bound_from: UNBOUND/open/VALUATIONS/CHARL_VAN_DUYKER_VALUATIONS/grobler_abbey_valuation"
        in status
    )
    assert not unbound_dir.exists()
