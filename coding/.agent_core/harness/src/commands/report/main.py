from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state import logs
from src.state.user_mappings import load_all
from src.utils.gitignore import ensure_agent_core_tmp_ignored
from src.utils.markdown import slugify


app = typer.Typer(help="Generate management work reports", invoke_without_command=True, no_args_is_help=True)


def _last_completed_work_week(reference: date) -> tuple[date, date]:
    current_monday = reference - timedelta(days=reference.weekday())
    if reference.weekday() >= 5:
        start = current_monday
    else:
        start = current_monday - timedelta(days=7)
    return start, start + timedelta(days=4)


def _report_filename(username: str, start: date) -> str:
    year, week, _weekday = start.isocalendar()
    return f"{slugify(username)}_{year}W{week:02d}_report.md"


def _matching_logs(username: str, start: date, end: date) -> list[logs.WorkLog]:
    log_username = slugify(username)
    records = [
        record
        for record in logs.list_all(limit=1000, username=log_username)
        if start <= datetime.fromisoformat(record.created_at).date() <= end
    ]
    return sorted(records, key=lambda item: item.created_at)


def _format_source_logs(records: list[logs.WorkLog]) -> list[str]:
    if not records:
        return [
            "No work logs were found for this user in the selected work week.",
            "",
            "This absence is evidence. The completed report must say that there is no logged work for the period.",
        ]

    lines: list[str] = []
    for record in records:
        lines.extend(
            [
                f"### {record.filename}",
                "",
                f"- Created: {record.created_at}",
                f"- User: {record.username}",
                f"- Spec: {record.spec_slug or 'N/A'}",
                "",
                "````text",
                record.body.strip(),
                "````",
                "",
            ]
        )
    return lines


def _report_template(username: str, start: date, end: date, records: list[logs.WorkLog]) -> str:
    source_logs = "\n".join(_format_source_logs(records))
    return f"""# Management Work Report - {username}

## Agent Instructions

You must complete this report for management using the source work logs below.

Assess the work honestly and critically. Do not inflate impact, polish weak evidence, or assume work happened because the prose sounds busy. If a log contains fluff, planning without execution, repeated context gathering, unresolved blockers, or non-work, call that out in the report.

Base the report primarily on the work logs. You may inspect files mentioned in the logs when needed to understand the work, but do not inspect git history, git diffs, git blame, commits, or pull requests. This must stay a management oversight report, not a forensic code audit.

Remember that many small logs do not imply high productivity, and one dense log may represent more useful work than many shallow logs. Score the observed work, not the volume of writing.

Replace every placeholder below. Keep the final report direct, specific, and evidence-based.

## Scope

- GitHub user: {username}
- Log username: {slugify(username)}
- Work week: {start.isoformat()} to {end.isoformat()} inclusive
- Work logs found: {len(records)}

## Final Report

### Executive Summary

{{Write a concise management summary of what this user appears to have accomplished during the work week.}}

### Material Work Observed

{{List the concrete work that appears to have been done. Focus on outcomes, shipped changes, resolved blockers, decisions captured, and durable project artifacts.}}

### Low-Value Or Non-Work Observed

{{List fluff, administrative churn, repeated context gathering, vague claims, unresolved work presented as progress, or other low-value activity. If none is evident, say so explicitly and explain why.}}

### Blockers And Risks

{{List blockers, unresolved errors, risky assumptions, or areas where the logs do not provide enough evidence.}}

### Productivity Score

Score: {{0-10}}

Rationale: {{Be critical. Score tangible useful output and follow-through, not number of logs or confidence of wording.}}

### Relevance Score

Score: {{0-10}}

Rationale: {{Be critical. Score alignment with project priorities, active tasks/specs/todos, and work that materially moved the repository forward.}}

### Evidence Notes

{{Reference the specific work log filenames and details that support the assessment.}}

## Source Work Logs

{source_logs}
"""


def _write_report(username: str, start: date, end: date, records: list[logs.WorkLog]) -> Path:
    temp_dir = PROJECT_PATHS.state_root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    output_path = temp_dir / _report_filename(username, start)
    output_path.write_text(_report_template(username, start, end, records))
    return output_path


@app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    username: Annotated[str | None, typer.Argument(help="Mapped GitHub username to report on.")] = None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if username is None:
        typer.echo("Report requires a mapped GitHub username.", err=True)
        typer.echo("Run: python -B .agent_core/harness/main.py report <github_username>", err=True)
        raise typer.Exit(code=1)

    mappings = load_all()
    if username not in mappings:
        typer.echo(f"GitHub user '{username}' is not mapped in {PROJECT_PATHS.user_mappings_file_display}.", err=True)
        typer.echo(f"Add a [{username}] section before generating a management report for that user.", err=True)
        raise typer.Exit(code=1)

    start, end = _last_completed_work_week(date.today())
    records = _matching_logs(username, start, end)
    output_path = _write_report(username, start, end, records)

    try:
        ensure_agent_core_tmp_ignored(PROJECT_PATHS.project_root / ".gitignore")
    except OSError as error:
        typer.echo(f"Warning: could not ensure Agent Core .gitignore state rules: {error}", err=True)

    typer.echo(f"Management report draft created: {output_path.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo(f"Work week: {start.isoformat()} to {end.isoformat()}")
    typer.echo(f"Work logs found: {len(records)}")
    typer.echo("")
    typer.echo("You must read the report draft, replace every placeholder, and evaluate the observed work critically.")
    typer.echo("Do not inspect git history, git diffs, git blame, commits, or pull requests for this report.")
    typer.echo("You may inspect files mentioned in the work logs only when needed to understand impact.")
