from datetime import datetime
from pathlib import Path

from src.commands.onboard.formatting import file, heading, subsection
from src.config.branches import get_branch_names
from src.config.main import load_project_config, summarize_validation_error
from src.config.models import AgentCoreConfig
from src.config.paths import PROJECT_PATHS
from src.state import logs, memories, specs, tasks, todos
from src.state.models import Spec, Task, Todo, WorkLog
from src.utils import git, worktrees


def read_text(path: Path) -> str:
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return "[Skipped binary or non-text file]"
    except OSError as error:
        return f"[Could not read file: {error}]"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def _iter_docs() -> list[Path]:
    if not PROJECT_PATHS.docs_dir.exists():
        return []
    return sorted(
        (path for path in PROJECT_PATHS.docs_dir.rglob("*") if path.is_file()),
        key=lambda path: relative(path).lower(),
    )


def _file_body(path: Path) -> str:
    return read_text(path).strip()


def _important_files_section(config: AgentCoreConfig) -> list[str]:
    file_sections: list[str] = []
    for item in config.files:
        body = _file_body(PROJECT_PATHS.project_root / item.path)
        if not body:
            continue
        file_sections.extend(file(item.path))
        if item.description:
            file_sections.append(f"*{item.description}*")
            file_sections.append("")
        file_sections.append(body)
        file_sections.append("")

    if not file_sections:
        return []
    return [*subsection("📄 IMPORTANT FILES"), *file_sections]


def _tree_dir(path: Path, max_entries: int = 300) -> str:
    if not path.exists():
        return f"{relative(path)} (not found)"
    if not path.is_dir():
        return f"{relative(path)} (not a directory)"

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
        entries.append(relative(child) + ("/" if child.is_dir() else ""))
    return "\n".join(entries)


def _tree_sections(config: AgentCoreConfig) -> list[str]:
    tree_sections: list[str] = []
    for item in config.tree_dirs:
        tree = _tree_dir(PROJECT_PATHS.project_root / item.path).strip()
        if not tree:
            continue
        tree_sections.extend(file(item.path))
        if item.description:
            tree_sections.append(f"*{item.description}*")
            tree_sections.append("")
        tree_sections.append("```text")
        tree_sections.append(tree)
        tree_sections.append("```")
        tree_sections.append("")

    if not tree_sections:
        return []
    return [*subsection("🌲 DIRECTORY TREES"), *tree_sections]


def _docs_section() -> list[str]:
    doc_sections: list[str] = []
    for path in _iter_docs():
        body = _file_body(path)
        if not body:
            continue
        doc_sections.extend(file(relative(path)))
        doc_sections.append(body)
        doc_sections.append("")

    if not doc_sections:
        return []
    return [*subsection("📚 PROJECT DOCS"), *doc_sections]


def _spec_preview(record: Spec, max_chars: int = 300) -> str:
    body = record.body.strip()
    if len(body) <= max_chars:
        return body
    return f"{body[:max_chars]}..."


def _format_task_detail(record: Task) -> list[str]:
    lines = [f"> **{record.title}**"]
    body = record.body.strip()
    if body:
        lines.extend(["", body])
    return lines


def _branch_diff_stat() -> tuple[str, str] | None:
    branches = get_branch_names()
    command = f"git diff origin/{branches.dev} --stat"
    result = git.run_git(["diff", f"origin/{branches.dev}", "--stat"], check=False)
    if result.returncode == 0:
        return command, result.stdout.rstrip()

    command = f"git diff {branches.dev} --stat"
    result = git.run_git(["diff", branches.dev, "--stat"], check=False)
    if result.returncode == 0:
        return command, result.stdout.rstrip()
    return None


def _format_active_spec(record: Spec) -> list[str]:
    lines = subsection(f"📋 ACTIVE SPEC: {record.title}")
    lines.append(
        "You are currently working on this spec. Complete its tasks, then run:"
    )
    lines.append(
        f'`python -B .agent_core/harness/main.py spec complete {record.slug} "detailed commit message"`'
    )
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
            lines.append("")
            for index, task_record in enumerate(pending):
                if index > 0:
                    lines.append("")
                lines.extend(_format_task_detail(task_record))

    lines.append("")
    return lines


def _log_entry(record: WorkLog) -> str:
    lines = [
        *file(f"🧾 {record.filename}"),
        f"> Date: {record.created_at}",
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


def _git_state_section(branch: str, active_spec: Spec | None) -> list[str]:
    lines = subsection("🌿 GIT STATE")
    lines.append(f"**Current Branch:** {branch}")

    branches = get_branch_names()
    parent = branches.noswitch_branches.parent_for(branch)
    if parent is not None:
        lines.append(f"**Noswitch Branch:** rebasing onto `{parent}`")
    elif branch.startswith(f"{branches.dev}-"):
        lines.append(f"**Spec Branch:** rebasing onto `origin/{branches.dev}`")

    if active_spec is not None:
        diff_stat = _branch_diff_stat()
        if diff_stat is not None:
            diff_command, diff_output = diff_stat
            lines.append("")
            lines.append(f"**Spec Changes:** `{diff_command}`")
            lines.append("```text")
            lines.append(
                diff_output
                if diff_output
                else "No file changes relative to the dev branch."
            )
            lines.append("```")
    lines.append("")
    return lines


def _available_specs_section() -> list[str]:
    lines = subsection("📋 AVAILABLE SPECS")
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
        lines.append(
            "Run `python -B .agent_core/harness/main.py merge pr` to merge a PR."
        )
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
                completed = sum(
                    1 for item in task_records if item.status == "completed"
                )
                lines.append("")
                lines.append(f"Tasks: {completed}/{len(task_records)} completed")
            lines.append("")
    elif not merge_ready_specs:
        lines.append(
            'No specs available. Create one with `python -B .agent_core/harness/main.py spec new "title"`.'
        )
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
    memory_records = memories.list_all()
    if not memory_records:
        return []

    lines = subsection("💾 PROJECT MEMORIES")
    lines.append(
        "These are project-specific memories: patterns, conventions, and preferences "
        "to keep in mind while working on this codebase."
    )
    lines.append("")
    for record in memory_records:
        lines.append(f"> ## {record.title}")
        lines.append("")
        body = record.body.strip()
        if body:
            lines.append(body)
        lines.append("")
    return lines


def _work_logs_section(active_spec: Spec | None) -> list[str]:
    lines = subsection("📝 RECENT WORK LOGS")
    if active_spec is not None:
        lines.append(
            "This is a dedicated spec worktree. Only work logs linked to "
            f"`{active_spec.slug}` appear here; general project logs are intentionally excluded."
        )
    else:
        lines.append(
            "No spec is currently active. This section shows recent project work logs, "
            "with the current user's logs first."
        )
    lines.append("")

    log_records = _recent_log_records(active_spec)
    if log_records:
        for record in log_records:
            lines.append(_log_entry(record))
            lines.append("")
    elif active_spec is not None:
        lines.append(
            "No spec work logs exist yet. After meaningful work has been done, "
            "create one with `python -B .agent_core/harness/main.py log new`."
        )
        lines.append("")
    else:
        lines.append(
            "No project work logs exist yet. After meaningful work has been done, create one with "
            "`python -B .agent_core/harness/main.py log new`."
        )
        lines.append("")
    return lines


def _open_todos_section(records: list[Todo]) -> list[str]:
    if not records:
        return []

    lines = subsection("📌 OPEN TODOS")
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
    lines.append(
        '- Claim a todo: `python -B .agent_core/harness/main.py todo claim "<title or slug>" <user>`'
    )
    lines.append(
        '- Create new todo: `python -B .agent_core/harness/main.py todo new "title" "description"`'
    )
    lines.append("- List all todos: `python -B .agent_core/harness/main.py todo list`")
    lines.append("")
    return lines


def _workflow_hints_section(active_spec: Spec | None) -> list[str]:
    lines = subsection("💡 AGENT WORKFLOW HINTS")
    if active_spec is not None:
        lines.append("Working with tasks:")
        lines.append(
            '- Create task: `python -B .agent_core/harness/main.py task new "title" "detailed description"`'
        )
        lines.append(
            "- Complete task: `python -B .agent_core/harness/main.py task complete <task_slug> "
            '"detailed notes"`'
        )
        lines.append("- List tasks: `python -B .agent_core/harness/main.py task list`")
        lines.append(
            "- Pass `--spec <spec_slug>` only when intentionally managing another spec from outside its worktree."
        )
        lines.append("")
        lines.append("Important workflow rules:")
        lines.append(
            "- Complete one task at a time, then stop and await further instructions."
        )
        lines.append("- Mark each task complete as soon as you finish it.")
        lines.append("- Do not batch task completions.")
        lines.append(
            f'- When all tasks are done, run: `python -B .agent_core/harness/main.py spec complete {active_spec.slug} "detailed commit message"`'
        )
    else:
        lines.append(
            "Choose a spec worktree or ask the user which todo/spec to handle next."
        )
    lines.append("")
    return lines


def _next_steps_section(active_spec: Spec | None, open_todos: list[Todo]) -> list[str]:
    lines = subsection("👉 SUGGESTED NEXT STEPS")
    if active_spec is not None:
        pending = [
            record
            for record in tasks.list_all(active_spec.slug)
            if record.status != "completed"
        ]
        if pending:
            next_task = pending[0]
            lines.append(f"1. Work on the next open task: **{next_task.title}**")
        else:
            lines.append(
                f'1. Finalize the spec and run the completion command: `python -B .agent_core/harness/main.py spec complete {active_spec.slug} "detailed commit message"`'
            )
    else:
        lines.append(
            '1. Create a new spec: `python -B .agent_core/harness/main.py spec new "feature name"`'
        )
        if open_todos:
            lines.append(
                '2. Or work on a todo: `python -B .agent_core/harness/main.py todo claim "<title or slug>" <user>`'
            )
    lines.append("")
    lines.append("Remember to create a work log at the end of your session:")
    lines.append("`python -B .agent_core/harness/main.py log new`")
    lines.append("")
    return lines


def _sync_warning_section(sync_warning: str) -> list[str]:
    lines = subsection("🚨 ONBOARD SYNC WARNING")
    lines.append(
        "The default sync step failed, but onboard context was still generated."
    )
    lines.append(f"Reason: {sync_warning}")
    lines.append("")
    lines.append("Report this warning to the user before doing any other work.")
    lines.append("")
    return lines


def _agent_instruction_section(
    sync_warning: str | None,
    active_spec: Spec | None,
    open_todos: list[Todo],
) -> list[str]:
    lines = subsection("⚠️ AGENT INSTRUCTION")
    lines.append("Your next response must:")
    item_number = 1
    if sync_warning is not None:
        lines.append(f"{item_number}. Report the onboard sync warning and its reason.")
        item_number += 1

    if active_spec is not None:
        lines.append(
            f"{item_number}. State that this is the `{active_spec.slug}` spec worktree and summarize its current task state."
        )
        item_number += 1
    else:
        lines.append(f"{item_number}. State that no spec is currently active.")
        item_number += 1
        if open_todos:
            lines.append(
                f"{item_number}. Mention that open todos are available and must be claimed before work starts."
            )
            item_number += 1

    lines.append(
        f"{item_number}. Summarize the current project state. Use tables where appropriate and make it look nice. Be concise, yet informative."
    )
    item_number += 1
    lines.append(f"{item_number}. Ask the user how they would like to proceed.")
    lines.append("")
    lines.append(
        "Do not start implementation work until the user gives explicit instruction."
    )
    lines.append("")
    return lines


def _codebase_and_conventions_section(config: AgentCoreConfig) -> list[str]:
    lines = heading("📋 CODEBASE AND CONVENTIONS")
    lines.append(f"**Project:** {config.project.name}")
    description = config.project.description.strip()
    if description:
        lines.append(f"**Description:** {description}")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append("")
    lines.extend(_important_files_section(config))
    lines.extend(_tree_sections(config))
    lines.extend(_docs_section())
    lines.extend(_memories_section())
    return lines


def _onboard_output_section(sync_warning: str | None) -> list[str]:
    branch = _current_branch()
    active_spec = _active_spec_for_branch(branch)
    open_todos = todos.list_all(status="open")

    lines = heading("📄 ONBOARD OUTPUT")
    lines.extend(_git_state_section(branch, active_spec))
    if sync_warning is not None:
        lines.extend(_sync_warning_section(sync_warning))

    if active_spec is not None:
        lines.extend(_format_active_spec(active_spec))
    else:
        lines.extend(_available_specs_section())

    lines.extend(_work_logs_section(active_spec))

    if active_spec is None:
        lines.extend(_open_todos_section(open_todos))

    lines.extend(_workflow_hints_section(active_spec))
    lines.extend(_next_steps_section(active_spec, open_todos))
    lines.extend(_agent_instruction_section(sync_warning, active_spec, open_todos))
    return lines


def build_context(sync_warning: str | None = None) -> str:
    result = load_project_config(PROJECT_PATHS.config_file)
    if result.config is None:
        if result.validation_error is not None:
            summary = summarize_validation_error(result.validation_error)
            raise ValueError(f"Invalid {PROJECT_PATHS.config_file_display}:\n{summary}")
        raise ValueError(f"Missing or empty {PROJECT_PATHS.config_file_display}")

    lines = _codebase_and_conventions_section(result.config)
    lines.extend(_onboard_output_section(sync_warning))
    return "\n".join(lines).rstrip() + "\n"
