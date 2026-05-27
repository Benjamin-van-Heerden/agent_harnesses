from pathlib import Path

from helpers import harness_command, run_command, run_setup


def test_bookkeeping_commands_create_chronology_obligations_and_todos(
    tmp_path: Path,
) -> None:
    target = tmp_path / "practice"
    target.mkdir()
    run_setup(target)

    harness = harness_command()
    run_command(
        [*harness, "client", "new", "Smith Corp", "entity", "--slug", "smith"],
        cwd=target,
    )
    run_command(
        [
            *harness,
            "matter",
            "new",
            "smith",
            "litigation",
            "shareholder_dispute",
            "high",
            "hourly",
        ],
        cwd=target,
    )
    matter_dir = next((target / "ZZ_CLIENTS" / "smith" / "matters" / "open").iterdir())

    deadline = run_command(
        [
            *harness,
            "obligation",
            "add",
            "deadline",
            "shareholder_dispute",
            "answering_affidavit",
            "2999-05-21",
            "filing — Answering affidavit",
        ],
        cwd=target,
    )
    assert "Added obligation: deadline due 2999-05-21" in deadline.stdout
    obligations = list(
        (matter_dir / "info" / "obligations" / "deadline").glob("*.toml")
    )
    assert len(obligations) == 1
    assert 'kind = "deadline"' in obligations[0].read_text()
    assert 'description = "filing — Answering affidavit"' in obligations[0].read_text()
    status_text = (matter_dir / "info" / "status.md").read_text()
    assert "next_obligation:" in status_text
    assert "2999-05-21" in status_text

    invalid_deadline = run_command(
        [
            *harness,
            "obligation",
            "add",
            "deadline",
            "shareholder_dispute",
            "bad_date",
            "21-05-2999",
            "Bad date",
        ],
        cwd=target,
        check=False,
    )
    assert invalid_deadline.returncode == 1
    assert "date must be YYYY-MM-DD" in invalid_deadline.stderr

    communication = run_command(
        [
            *harness,
            "chronology",
            "add",
            "email",
            "shareholder_dispute",
            "2026-05-21",
            "in",
            "Jones",
            "Settlement proposal",
        ],
        cwd=target,
    )
    assert "Added chronology event: email" in communication.stdout

    invalid_direction = run_command(
        [
            *harness,
            "chronology",
            "add",
            "email",
            "shareholder_dispute",
            "2026-05-21",
            "sideways",
            "Jones",
            "Bad direction",
        ],
        cwd=target,
        check=False,
    )
    assert invalid_direction.returncode == 1
    assert "direction must be 'in' or 'out'" in invalid_direction.stderr

    note = run_command(
        [
            *harness,
            "chronology",
            "add",
            "note",
            "shareholder_dispute",
            "2026-05-21",
            "Internal note",
            "Longer body",
        ],
        cwd=target,
    )
    assert "Added chronology event: note" in note.stdout
    chronology_files = list((matter_dir / "info" / "chronology").glob("*/*.toml"))
    assert any(
        'kind = "email"' in path.read_text() and "Jones" in path.read_text()
        for path in chronology_files
    )
    assert any('kind = "note"' in path.read_text() for path in chronology_files)

    global_todo = run_command(
        [*harness, "todo", "new", "review_rules", "Review court rules", "normal"],
        cwd=target,
    )
    assert "Created global todo: review_rules" in global_todo.stdout
    global_todo_file = target / ".praxis" / "todos" / "open" / "review_rules.md"
    assert global_todo_file.is_file()

    matter_todo = run_command(
        [
            *harness,
            "todo",
            "new",
            "draft_affidavit",
            "Draft affidavit",
            "high",
            "shareholder_dispute",
        ],
        cwd=target,
    )
    assert "Created matter todo: draft_affidavit" in matter_todo.stdout
    matter_todo_file = matter_dir / "info" / "todos" / "draft_affidavit.md"
    assert matter_todo_file.is_file()

    invalid_todo = run_command(
        [*harness, "todo", "new", "bad_priority", "Bad priority", "urgent"],
        cwd=target,
        check=False,
    )
    assert invalid_todo.returncode == 1
    assert "invalid priority 'urgent'" in invalid_todo.stderr

    claimed = run_command(
        [*harness, "todo", "claim", "draft_affidavit", "shareholder_dispute"],
        cwd=target,
    )
    assert "Claimed todo: draft_affidavit" in claimed.stdout
    assert not matter_todo_file.exists()
    claimed_file = matter_dir / "info" / "todos" / "claimed" / "draft_affidavit.md"
    assert claimed_file.is_file()
    assert "status: claimed" in claimed_file.read_text()

    memory = run_command(
        [*harness, "memory", "new", "affidavit_style", "Affidavit style"], cwd=target
    )
    assert "Created memory: affidavit_style" in memory.stdout
    memory_file = (
        target / ".praxis" / "local_context" / "memories" / "affidavit_style.md"
    )
    assert memory_file.is_file()
    assert "_TODO_" in memory_file.read_text()

    work_log = run_command([*harness, "log", "new", "shareholder_dispute"], cwd=target)
    assert "Created work log:" in work_log.stdout
    assert "replace every TODO" in work_log.stdout
    log_files = list((target / ".praxis" / "local_context" / "logs").glob("*.md"))
    assert len(log_files) == 1
    assert "matter: ZZ_CLIENTS/smith/matters/open/" in log_files[0].read_text()

    obligation = run_command(
        [*harness, "obligation", "list", "shareholder_dispute"], cwd=target
    )
    assert "deadline\topen\tfiling — Answering affidavit" in obligation.stdout
