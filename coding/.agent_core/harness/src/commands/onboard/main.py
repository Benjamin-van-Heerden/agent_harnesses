import typer

from src.commands.onboard.assigned_worktrees import (
    AssignedWorktreeResult,
    create_missing_for_authenticated_user,
)
from src.commands.onboard.content import build_context, relative
from src.commands.onboard.mutations import (
    render_mutation_summary,
    snapshot_agent_core,
    summarize_mutations,
)
from src.commands.onboard.output import write_output
from src.commands.onboard.preflight import (
    OnboardBlockedError,
    OnboardRestartRequired,
    no_sync_escape_hatch_lines,
    run_git_preflight,
    sync_warning_from_exit,
)
from src.commands.sync.main import sync_all
from src.config.branches import get_branch_names
from src.config.main import load_project_config, summarize_validation_error
from src.config.paths import PROJECT_PATHS
from src.state.user_mappings import ensure_user_mappings_file
from src.utils import auto_update, git, worktrees
from src.utils.errors import GitError, GitHubError
from src.utils.gitignore import ensure_agent_core_tmp_ignored, ensure_symlink_paths_ignored

app = typer.Typer(help="Build local project context")


def _ensure_tmp_ignored() -> None:
    try:
        if ensure_agent_core_tmp_ignored(PROJECT_PATHS.project_root / ".gitignore"):
            typer.echo("Onboard applied .gitignore patch: ensured Agent Core state is tracked except .agent_core/tmp/ and .cache/pycache/ is ignored.")
    except OSError as error:
        typer.echo(f"Warning: could not ensure Agent Core .gitignore state rules: {error}", err=True)


def _main_repo_non_dev_branch_message() -> str | None:
    if worktrees.is_worktree():
        return None

    branch = git.current_branch()
    if branch is None:
        return None

    branches = get_branch_names()
    if branch == branches.dev:
        return None

    protected_note = ""
    if branch in branches.protected:
        protected_note = " This is a protected branch."

    return "\n".join(
        [
            "Onboard stopped before building project context.",
            f"Current branch: {branch}",
            "",
            f"This checkout is not on the configured development branch `{branches.dev}`.{protected_note}",
            "Normal development must not be done from this branch.",
            "The coding harness is designed to start from the configured development branch or from a dedicated spec worktree.",
            "",
            "Here be dragons.",
            "You must notify the user that onboarding was stopped because this session is on a non-development branch.",
            f"You must tell the user that the current branch is `{branch}` and ask them to confirm they deliberately want to work from this branch.",
            f"You must ask the user whether they want to switch back to the configured development branch. If they confirm, run `git switch {branches.dev}` and then run onboard again.",
            "If the user confirms they deliberately want to stay on this branch and gives explicit permission, run `python -B .agent_core/harness/main.py onboard --no-sync` so the session still has project context.",
            "Only continue from this branch if the user deliberately chose it and understands the consequences.",
            f"To resume the normal workflow, switch back to `{branches.dev}` and rerun onboard.",
            "",
            "No onboard context file was created.",
        ]
    )


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
    agent_core_before = snapshot_agent_core(PROJECT_PATHS.state_root)
    mutation_audit_reported = False

    def report_agent_core_mutations() -> None:
        nonlocal mutation_audit_reported
        if mutation_audit_reported:
            return
        mutation_audit_reported = True
        summary = summarize_mutations(
            agent_core_before,
            snapshot_agent_core(PROJECT_PATHS.state_root),
        )
        for line in render_mutation_summary(summary):
            typer.echo(line)

    sync_warning: str | None = None
    assigned_worktrees: list[AssignedWorktreeResult] = []
    try:
        config_result = load_project_config(PROJECT_PATHS.config_file)
        if config_result.config is None:
            if config_result.validation_error is not None:
                summary = summarize_validation_error(config_result.validation_error)
                typer.echo(f"Invalid {PROJECT_PATHS.config_file_display}:\n{summary}", err=True)
            else:
                typer.echo(f"Missing or empty {PROJECT_PATHS.config_file_display}", err=True)
            raise typer.Exit(code=1)

        if no_sync:
            try:
                if ensure_user_mappings_file():
                    typer.echo(f"Onboard mutated {PROJECT_PATHS.user_mappings_file_display}: ensured current mapping format.")
            except Exception as error:
                typer.echo(f"Warning: could not ensure {PROJECT_PATHS.user_mappings_file_display}: {error}", err=True)

        try:
            missing_ignores = ensure_symlink_paths_ignored(
                config_result.config,
                PROJECT_PATHS.project_root / ".gitignore",
            )
            if missing_ignores:
                typer.echo(
                    "Onboard mutated .gitignore: added configured worktree symlink ignores: "
                    + ", ".join(missing_ignores)
                )
        except ValueError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=1) from error

        if not no_sync:
            try:
                run_git_preflight(continue_requested)
            except OnboardRestartRequired as restart:
                typer.echo(str(restart))
                raise typer.Exit(code=0) from restart
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
            if update_result.skipped_reason:
                typer.echo(f"Harness auto-update skipped: {update_result.skipped_reason}")
            if update_result.reexec_required:
                typer.echo("Harness updated. Restarting onboard with the refreshed harness.")
                report_agent_core_mutations()
                auto_update.reexec_current_command()

            try:
                sync_all(no_git=False)
            except typer.Exit as error:
                if error.exit_code == 0:
                    raise
                sync_warning = sync_warning_from_exit(error)
                if isinstance(error.__cause__, GitError):
                    non_dev_branch_message = _main_repo_non_dev_branch_message()
                    if non_dev_branch_message is not None:
                        typer.echo(non_dev_branch_message, err=True)
                        raise typer.Exit(code=1) from error

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
                    typer.echo("", err=True)
                    for line in no_sync_escape_hatch_lines():
                        typer.echo(line, err=True)
                    raise typer.Exit(code=1) from error
                typer.echo(f"Onboard sync warning: {sync_warning}", err=True)
            except Exception as error:
                sync_warning = str(error)
                typer.echo(f"Onboard sync warning: {sync_warning}", err=True)

            if sync_warning is None:
                try:
                    assigned_worktrees = create_missing_for_authenticated_user()
                except (GitError, GitHubError, ValueError) as error:
                    typer.echo("Onboard stopped while creating assigned spec worktrees.", err=True)
                    typer.echo(str(error), err=True)
                    typer.echo("", err=True)
                    typer.echo(
                        "You must resolve the assigned worktree failure, then rerun onboard.",
                        err=True,
                    )
                    raise typer.Exit(code=1) from error

        try:
            content = build_context(sync_warning, assigned_worktrees)
        except ValueError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(code=1) from error

        if stdout or len(content) <= 14000:
            typer.echo(content)
            _ensure_tmp_ignored()
            report_agent_core_mutations()
            return

        output_path = write_output(content)
        _ensure_tmp_ignored()
        report_agent_core_mutations()
        typer.echo("")
        typer.echo(f"✅ Onboard context written to: {relative(output_path)}")
        typer.echo(f"📏 Line count: {content.count(chr(10))}")
        typer.echo("")
        typer.echo(
            "NB: YOU MUST read it in full before proceeding. No exceptions, the "
            "document contains important context. An overview or partial reading of "
            "the document is not enough, it must be read in its entirety (every line)."
        )
    finally:
        report_agent_core_mutations()
