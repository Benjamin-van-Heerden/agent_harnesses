from datetime import datetime, timedelta
from pathlib import Path

import typer
from src.commands.sync.main import sync_all
from src.config.branches import get_branch_names
from src.config.main import load_project_config, summarize_validation_error
from src.config.models import AgentCoreConfig, BranchNames
from src.config.paths import PROJECT_PATHS
from src.state import logs, memories, specs, tasks, todos
from src.state.models import Spec, Task, Todo, WorkLog
from src.utils import auto_update
from src.utils import git, worktrees
from src.utils.errors import GitError

app = typer.Typer(help="Build local project context")


class OnboardBlockedError(Exception):
    pass


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return "[Skipped binary or non-text file]"
    except OSError as error:
        return f"[Could not read file: {error}]"


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def _section(title: str) -> list[str]:
    return ["-" * 70, title, "-" * 70, ""]


def _iter_docs() -> list[Path]:
    if not PROJECT_PATHS.docs_dir.exists():
        return []
    return sorted(
        (path for path in PROJECT_PATHS.docs_dir.rglob("*") if path.is_file()),
        key=lambda path: _relative(path).lower(),
    )


def _important_files_section(config: AgentCoreConfig) -> list[str]:
    lines: list[str] = []
    if not config.files:
        return lines

    lines.extend(_section("📄 IMPORTANT FILES"))
    for item in config.files:
        path = PROJECT_PATHS.project_root / item.path
        lines.append(f"## {item.path}")
        if item.description:
            lines.append(f"*{item.description}*")
            lines.append("")
        lines.append(_read_text(path).strip())
        lines.append("")
    return lines


def _tree_dir(path: Path, max_entries: int = 300) -> str:
    if not path.exists():
        return f"{_relative(path)} (not found)"
    if not path.is_dir():
        return f"{_relative(path)} (not a directory)"

    entries: list[str] = []
    for index, child in enumerate(
        sorted(path.rglob("*"), key=lambda item: str(item).lower())
    ):
        if index >= max_entries:
            entries.append("...")
            break
        if any(
            part in {".git", ".venv", "__pycache__", "node_modules"}
            for part in child.parts
        ):
            continue
        entries.append(_relative(child) + ("/" if child.is_dir() else ""))
    return "\n".join(entries)


def _tree_sections(config: AgentCoreConfig) -> list[str]:
    lines: list[str] = []
    if not config.tree_dirs:
        return lines

    lines.extend(_section("🌲 DIRECTORY TREES"))
    for item in config.tree_dirs:
        path = PROJECT_PATHS.project_root / item.path
        lines.append(f"## {item.path}")
        if item.description:
            lines.append(f"*{item.description}*")
            lines.append("")
        lines.append("```text")
        lines.append(_tree_dir(path))
        lines.append("```")
        lines.append("")
    return lines


def _docs_section() -> list[str]:
    lines: list[str] = []
    docs = _iter_docs()
    if not docs:
        return lines

    lines.extend(_section("📚 PROJECT DOCS"))
    for path in docs:
        lines.append(f"## {_relative(path)}")
        lines.append("")
        lines.append(_read_text(path).strip())
        lines.append("")
    return lines


def _format_metadata(values: dict[str, object]) -> str:
    lines: list[str] = []
    for key, value in values.items():
        if value is None:
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _spec_preview(record: Spec, max_chars: int = 300) -> str:
    body = record.body.strip()
    if len(body) <= max_chars:
        return body
    return f"{body[:max_chars]}..."


def _format_task_detail(record: Task) -> list[str]:
    lines = [f"**{record.title}**"]
    body = record.body.strip()
    if body:
        lines.extend(["", body])
    return lines


def _format_active_spec(record: Spec) -> list[str]:
    lines = _section(f"📋 ACTIVE SPEC: {record.title}")
    lines.append("")
    lines.append("You are currently working on this spec. Complete its tasks, then run:")
    lines.append(
        f'`python -B .agent_core/harness/main.py spec complete {record.slug} "detailed commit message"`'
    )
    lines.append("")

    diff_stat = _branch_diff_stat()
    if diff_stat:
        lines.append("### Files modified in this spec (vs dev):")
        lines.append("```text")
        lines.append(diff_stat)
        lines.append("```")
        lines.append("")

    lines.append(f"Title: {record.title}")
    lines.append(f"Status: {record.status}")
    lines.append(f"Branch: {record.branch or 'N/A'}")
    if record.issue_url:
        lines.append(f"Issue: {record.issue_url}")
    if record.pr_url:
        lines.append(f"PR: {record.pr_url}")

    body = record.body.strip()
    if body:
        lines.append("")
        lines.append("### Details")
        lines.append("")
        lines.append(body)

    task_records = tasks.list_all(record.slug)
    if task_records:
        completed = [item for item in task_records if item.status == "completed"]
        pending = [item for item in task_records if item.status != "completed"]

        lines.append("")
        lines.append("### Tasks")

        if completed:
            lines.append("")
            lines.append(f"#### Completed ({len(completed)})")
            for task_record in completed:
                lines.append(f"- [x] {task_record.title}")

        if pending:
            lines.append("")
            lines.append(f"#### Pending ({len(pending)})")
            for task_record in pending:
                lines.append("")
                lines.extend(_format_task_detail(task_record))
                lines.append("")

    lines.append("")
    return lines


def _log_entry(record: WorkLog) -> str:
    lines = [
        f"### 🧾 {record.filename}",
        "",
        "```yaml",
        _format_metadata(
            {
                "filename": record.filename,
                "created_at": record.created_at,
                "date": record.date,
                "username": record.username,
                "spec_slug": record.spec_slug,
            }
        ),
        "```",
        "",
    ]
    body = record.body.strip()
    lines.append(body if body else "[Empty work log]")
    return "\n".join(lines)


def _recent_log_records(active_spec: Spec | None) -> list[WorkLog]:
    if active_spec is not None:
        return sorted(
            logs.list_all(limit=100, spec_slug=active_spec.slug),
            key=lambda item: item.created_at,
        )

    current_username = logs.current_username()
    selected: list[WorkLog] = []
    seen: set[str] = set()

    for record in logs.list_all(limit=3, username=current_username):
        selected.append(record)
        seen.add(record.filename)

    general_count = 0
    for record in logs.list_all(limit=20):
        if record.username == current_username:
            continue
        if record.filename in seen:
            continue
        selected.append(record)
        seen.add(record.filename)
        general_count += 1
        if general_count >= 5:
            break

    selected.sort(key=lambda item: item.created_at)
    return selected


def _current_branch() -> str:
    return git.current_branch() or "detached HEAD"


def _active_spec_for_branch(branch: str) -> Spec | None:
    for record in specs.list_all():
        if record.branch == branch and record.status in {"todo", "merge_ready"}:
            return record
    return None


def _branch_diff_stat() -> str:
    branches = get_branch_names()
    result = git.run_git(
        ["diff", "--stat", f"origin/{branches.dev}...HEAD"],
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    result = git.run_git(["diff", "--stat", branches.dev], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def _project_info_section(config: AgentCoreConfig, branch: str) -> list[str]:
    lines = _section("📁 PROJECT INFO")
    lines.append(f"**Project:** {config.project.name}")
    description = config.project.description.strip()
    if description:
        lines.append(f"**Description:** {description}")
    lines.append(f"**Current Branch:** {branch}")

    branches = get_branch_names()
    parent = branches.noswitch_branches.parent_for(branch)
    if parent is not None:
        lines.append(f"**Noswitch Branch:** rebasing onto `{parent}`")
    elif branch.startswith(f"{branches.dev}-"):
        lines.append(f"**Spec Branch:** rebasing onto `origin/{branches.dev}`")
    lines.append("")
    return lines


def _available_specs_section() -> list[str]:
    lines = _section("📋 AVAILABLE SPECS")
    lines.append("")
    lines.append("No spec is currently active. You are in the main repo.")
    lines.append("")

    spec_worktrees = [record for record in worktrees.list_all() if not record.is_main]
    if spec_worktrees:
        lines.append("### Active worktrees")
        lines.append("Each worktree is an isolated workspace for a spec.")
        for record in spec_worktrees:
            lines.append(f"- {record.path.name}: {record.path}")
        lines.append("")
        lines.append("To work on a spec, open a terminal in its worktree directory.")
        lines.append("")

    merge_ready_specs = specs.list_all(status="merge_ready")
    if merge_ready_specs:
        lines.append("### Specs ready to merge")
        for record in merge_ready_specs:
            lines.append(f"- {record.slug}: {record.title}")
            if record.pr_url:
                lines.append(f"  PR: {record.pr_url}")
        lines.append("")
        lines.append("Run `python -B .agent_core/harness/main.py merge pr` to merge a PR.")
        lines.append("")

    todo_specs = specs.list_all(status="todo")
    if todo_specs:
        lines.append("### Specs to work on")
        for record in todo_specs:
            lines.append(f"## {record.slug} ({record.status})")
            lines.append(f"Title: {record.title}")
            preview = _spec_preview(record)
            if preview:
                lines.append("")
                lines.append(preview)
            task_records = tasks.list_all(record.slug)
            if task_records:
                completed = sum(1 for item in task_records if item.status == "completed")
                lines.append("")
                lines.append(f"Tasks: {completed}/{len(task_records)} completed")
            lines.append("")
    elif not merge_ready_specs:
        lines.append('No specs available. Create one with `python -B .agent_core/harness/main.py spec new "title"`.')
        completed_specs = specs.list_all(status="completed")
        if completed_specs:
            lines.append("")
            lines.append("### Recently completed specs")
            for record in completed_specs[:2]:
                lines.append(f"**{record.slug}**: {record.title}")
                preview = _spec_preview(record, max_chars=500)
                if preview:
                    lines.append(preview)
                lines.append("")

    lines.append("")
    return lines


def _memories_section() -> list[str]:
    lines: list[str] = []
    memory_records = memories.list_all()
    if not memory_records:
        return lines

    lines.extend(_section("💾 PROJECT MEMORIES"))
    lines.append("")
    lines.append(
        "These are project-specific memories: patterns, conventions, and preferences "
        "to keep in mind while working on this codebase."
    )
    lines.append("")
    for record in memory_records:
        lines.append(f"### {record.title}")
        body = record.body.strip()
        if body:
            lines.append(body)
        lines.append("")
    return lines


def _work_logs_section(active_spec: Spec | None) -> list[str]:
    lines = _section("📝 RECENT WORK LOGS")
    lines.append("")
    lines.append(
        "Work logs capture what was accomplished in each session, blockers "
        "encountered, and suggested next steps. Review these to understand recent progress."
    )
    lines.append("")

    log_records = _recent_log_records(active_spec)
    if log_records:
        for record in log_records:
            lines.append(_log_entry(record))
            lines.append("")
    elif active_spec is not None:
        lines.append(
            f"No work logs for spec '{active_spec.slug}' yet. Create one with "
            "`python -B .agent_core/harness/main.py log new`."
        )
        lines.append("")
    else:
        lines.append(
            "No work logs yet. Create one with "
            "`python -B .agent_core/harness/main.py log new`."
        )
        lines.append("")
    return lines


def _open_todos_section(records: list[Todo]) -> list[str]:
    lines: list[str] = []
    if not records:
        return lines

    lines.extend(_section("📌 OPEN TODOS"))
    lines.append("")
    lines.append("These are standalone work items not tied to any spec.")
    lines.append("")
    for record in records:
        lines.append(f"### {record.title}")
        if record.issue_url:
            lines.append(record.issue_url)
        body = record.body.strip()
        if body:
            lines.append(body)
        lines.append("")
    lines.append("Commands:")
    lines.append('- Claim a todo: `python -B .agent_core/harness/main.py todo claim "<title or slug>" <user>`')
    lines.append('- Create new todo: `python -B .agent_core/harness/main.py todo new "title" "description"`')
    lines.append("- List all todos: `python -B .agent_core/harness/main.py todo list`")
    lines.append("")
    return lines


def _workflow_hints_section(active_spec: Spec | None) -> list[str]:
    lines = _section("💡 AGENT WORKFLOW HINTS")
    lines.append("")
    if active_spec is not None:
        lines.append("Working with tasks:")
        lines.append('- Create task: `python -B .agent_core/harness/main.py task new "title" "detailed description"`')
        lines.append('- Complete task: `python -B .agent_core/harness/main.py task complete <task_slug> "detailed notes"`')
        lines.append("- List tasks: `python -B .agent_core/harness/main.py task list`")
        lines.append(
            "- Pass `--spec <spec_slug>` only when intentionally managing another spec from outside its worktree."
        )
        lines.append("")
        lines.append("Important workflow rules:")
        lines.append("- Complete one task at a time, then stop and await further instructions.")
        lines.append("- Mark each task complete as soon as you finish it.")
        lines.append("- Do not batch task completions.")
        lines.append(
            f'- When all tasks are done, run: `python -B .agent_core/harness/main.py spec complete {active_spec.slug} "detailed commit message"`'
        )
    else:
        lines.append("Choose a spec worktree or ask the user which todo/spec to handle next.")
    lines.append("")
    return lines


def _next_steps_section(active_spec: Spec | None, open_todos: list[Todo]) -> list[str]:
    lines = _section("👉 SUGGESTED NEXT STEPS")
    lines.append("")
    if active_spec is not None:
        pending = [
            record for record in tasks.list_all(active_spec.slug) if record.status != "completed"
        ]
        if pending:
            lines.append(f"1. Continue working on: {pending[0].title}")
        else:
            lines.append(
                f'1. All tasks completed. Run: `python -B .agent_core/harness/main.py spec complete {active_spec.slug} "detailed commit message"`'
            )
    else:
        lines.append('1. Create a new spec: `python -B .agent_core/harness/main.py spec new "feature name"`')
        if open_todos:
            lines.append(
                '2. Or work on a todo: `python -B .agent_core/harness/main.py todo claim "<title or slug>" <user>`'
            )
    lines.append("")
    lines.append("Remember to create a work log at the end of your session:")
    lines.append("`python -B .agent_core/harness/main.py log new`")
    lines.append("")
    return lines


def _state_section(config: AgentCoreConfig) -> list[str]:
    branch = _current_branch()
    active_spec = _active_spec_for_branch(branch)
    open_todos = todos.list_all(status="open")

    lines = _project_info_section(config, branch)
    lines.extend(_section("📄 ONBOARD OUTPUT"))
    lines.append("")

    if active_spec is not None:
        lines.extend(_format_active_spec(active_spec))
    else:
        lines.extend(_available_specs_section())

    lines.extend(_memories_section())
    lines.extend(_work_logs_section(active_spec))

    if active_spec is None:
        lines.extend(_open_todos_section(open_todos))

    lines.extend(_workflow_hints_section(active_spec))
    lines.extend(_next_steps_section(active_spec, open_todos))
    return lines


def _sync_warning_section(sync_warning: str) -> list[str]:
    lines = _section("🚨 ONBOARD SYNC WARNING")
    lines.append(
        "The default sync step failed, but onboard context was still generated."
    )
    lines.append(f"Reason: {sync_warning}")
    lines.append("")
    lines.append("Report this warning to the user before doing any other work.")
    lines.append("")
    return lines


def _agent_instruction_section(sync_warning: str | None) -> list[str]:
    lines = _section("⚠️ AGENT INSTRUCTION")
    lines.append("")
    lines.append("Your next response must:")
    if sync_warning is not None:
        lines.append("1. Report the onboard sync warning and its reason.")
        lines.append("2. Briefly summarize the current project state.")
        lines.append("3. Ask the user how they would like to proceed.")
    else:
        lines.append("1. Briefly summarize the current project state.")
        lines.append("2. Ask the user how they would like to proceed.")
    lines.append("")
    lines.append(
        "Do not start implementation work until the user gives explicit instruction."
    )
    lines.append("")
    return lines


def _build_context(sync_warning: str | None = None) -> str:
    result = load_project_config(PROJECT_PATHS.config_file)
    if result.config is None:
        if result.validation_error is not None:
            summary = summarize_validation_error(result.validation_error)
            raise ValueError(f"Invalid {PROJECT_PATHS.config_file_display}:\n{summary}")
        raise ValueError(f"Missing or empty {PROJECT_PATHS.config_file_display}")

    config = result.config
    lines = [
        "=" * 70,
        "📋 PROJECT CONTEXT",
        "=" * 70,
        "",
        f"**Project:** {config.project.name}",
        f"**Description:** {config.project.description}",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
    ]

    if sync_warning is not None:
        lines.extend(_sync_warning_section(sync_warning))
    lines.extend(_important_files_section(config))
    lines.extend(_tree_sections(config))
    lines.extend(_docs_section())
    lines.extend(_state_section(config))
    lines.extend(_agent_instruction_section(sync_warning))
    return "\n".join(lines).rstrip() + "\n"


def _write_output(content: str) -> Path:
    temp_dir = PROJECT_PATHS.state_root / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    cutoff = datetime.now() - timedelta(hours=1)
    for path in temp_dir.glob("onboard_*.md"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                path.unlink()
        except OSError:
            pass

    output_path = temp_dir / f"onboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    output_path.write_text(content)
    return output_path


def _sync_warning_from_exit(error: typer.Exit) -> str:
    cause = error.__cause__
    if cause is not None:
        return str(cause)
    return f"Sync failed with exit code {error.exit_code}."


def _sync_target_branch(branch: str, branches: BranchNames) -> str:
    parent = branches.noswitch_branches.parent_for(branch)
    if parent is not None:
        return parent
    if branch.startswith(f"{branches.dev}-"):
        return branches.dev
    return branch


def _commit_count(revision_range: str) -> int | None:
    result = git.run_git(["rev-list", "--count", revision_range], check=False)
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def _remote_status_summary(branch: str, branches: BranchNames) -> str:
    target = _sync_target_branch(branch, branches)
    remote_ref = f"origin/{target}"
    if not git.remote_branch_exists(target):
        return f"Remote check: `{remote_ref}` does not exist."

    remote_only = _commit_count(f"HEAD..{remote_ref}")
    local_only = _commit_count(f"{remote_ref}..HEAD")
    if remote_only is None or local_only is None:
        return f"Remote check: could not compare `HEAD` with `{remote_ref}`."

    if target != branch:
        return (
            f"Remote check: current branch `{branch}` syncs against `{remote_ref}`; "
            f"{remote_only} remote commit(s) and {local_only} local commit(s) differ."
        )
    if remote_only and local_only:
        return (
            f"Remote check: `{branch}` has diverged from `{remote_ref}` "
            f"({local_only} local commit(s), {remote_only} remote commit(s))."
        )
    if remote_only:
        return (
            f"Remote check: `{branch}` is behind `{remote_ref}` by "
            f"{remote_only} commit(s)."
        )
    if local_only:
        return (
            f"Remote check: `{branch}` is ahead of `{remote_ref}` by "
            f"{local_only} commit(s)."
        )
    return f"Remote check: `{branch}` is up to date with `{remote_ref}`."


def _status_lines(max_lines: int = 20) -> list[str]:
    result = git.run_git(["status", "--short"], check=False)
    lines = result.stdout.splitlines()
    if len(lines) <= max_lines:
        return lines
    return [*lines[:max_lines], f"... {len(lines) - max_lines} more file(s)"]


def _dirty_worktree_message(continue_requested: bool) -> str:
    branch = git.current_branch() or "detached HEAD"
    try:
        remote_status = _remote_status_summary(branch, get_branch_names())
    except (GitError, ValueError) as error:
        remote_status = f"Remote check failed after fetch: {error}"

    lines = ["Onboard stopped before building project context."]
    if continue_requested:
        lines.append("`--continue` was requested, but the working tree is still dirty.")
    lines.append(remote_status)
    lines.append("The working tree has uncommitted changes:")
    for line in _status_lines():
        lines.append(f"  {line}")
    lines.extend(
        [
            "",
            "You must resolve these changes before onboarding can continue.",
            "Commit, stash, or discard the local changes, then run:",
            "  python -B .agent_core/harness/main.py onboard --continue",
            "",
            "No onboard context file was created because local context may be stale.",
        ]
    )
    return "\n".join(lines)


def _run_git_preflight(continue_requested: bool) -> None:
    try:
        git.fetch()
    except GitError as error:
        raise OnboardBlockedError(
            "\n".join(
                [
                    "Onboard stopped before building project context.",
                    f"Remote fetch failed: {error}",
                    "",
                    "You must resolve git connectivity or remote configuration before onboarding can continue.",
                    "Then run:",
                    "  python -B .agent_core/harness/main.py onboard --continue",
                    "",
                    "No onboard context file was created because remote context could not be verified.",
                ]
            )
        ) from error

    if git.has_uncommitted_changes():
        raise OnboardBlockedError(_dirty_worktree_message(continue_requested))


@app.callback(invoke_without_command=True)
def run(
    stdout: bool = typer.Option(
        False,
        "--stdout",
        help="Print full context to stdout.",
    ),
    no_sync: bool = typer.Option(
        False,
        "--no-sync",
        help="Skip default git/GitHub sync before building context.",
    ),
    continue_requested: bool = typer.Option(
        False,
        "--continue",
        help="Continue onboarding after resolving a prior git preflight block.",
    ),
) -> None:
    sync_warning: str | None = None
    if not no_sync:
        try:
            _run_git_preflight(continue_requested)
        except OnboardBlockedError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=1) from error

        try:
            update_result = auto_update.maybe_update()
        except auto_update.AutoUpdateError as error:
            typer.echo("Onboard stopped before building project context.", err=True)
            typer.echo(f"Harness auto-update failed: {error}", err=True)
            typer.echo("", err=True)
            typer.echo(
                "You must resolve the harness update failure, or set AGENT_CORE_SKIP_AUTO_UPDATE=1 and rerun onboard.",
                err=True,
            )
            raise typer.Exit(code=1) from error
        if update_result.reexec_required:
            typer.echo("Harness updated. Restarting onboard with the refreshed harness.")
            auto_update.reexec_current_command()

        try:
            sync_all(no_git=False)
        except typer.Exit as error:
            if error.exit_code == 0:
                raise
            sync_warning = _sync_warning_from_exit(error)
            if isinstance(error.__cause__, GitError):
                typer.echo("Onboard stopped before building project context.", err=True)
                typer.echo(f"Reason: {sync_warning}", err=True)
                typer.echo("", err=True)
                typer.echo(
                    "You must resolve git state before onboarding can continue.",
                    err=True,
                )
                typer.echo(
                    "Then run: python -B .agent_core/harness/main.py onboard --continue",
                    err=True,
                )
                raise typer.Exit(code=1) from error
            typer.echo(f"Onboard sync warning: {sync_warning}", err=True)
        except Exception as error:
            sync_warning = str(error)
            typer.echo(f"Onboard sync warning: {sync_warning}", err=True)

    try:
        content = _build_context(sync_warning)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    if stdout or len(content) <= 14000:
        typer.echo(content)
        return

    output_path = _write_output(content)
    typer.echo(f"✅ Onboard context written to: {_relative(output_path)}")
    typer.echo(f"📏 Line count: {content.count(chr(10))}")
    typer.echo("")
    typer.echo(
        "NB: YOU MUST read it in full before proceeding. No exceptions, the "
        "document contains important context. An overview or partial reading of "
        "the document is not enough, it must be read in its entirety (every line)."
    )
