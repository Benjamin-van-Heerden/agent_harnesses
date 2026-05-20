import typer

from src.commands.onboard.assigned_worktrees import (
    AssignedWorktreeResult,
    create_missing_for_authenticated_user,
)
from src.commands.onboard.content import build_context, relative
from src.commands.onboard.output import write_output
from src.commands.onboard.preflight import (
    OnboardBlockedError,
    run_git_preflight,
    sync_warning_from_exit,
)
from src.config.main import load_project_config, summarize_validation_error
from src.config.paths import PROJECT_PATHS
from src.commands.sync.main import sync_all
from src.utils import auto_update
from src.utils.errors import GitError, GitHubError
from src.utils.gitignore import ensure_symlink_paths_ignored

app = typer.Typer(help="Build local project context")


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
    assigned_worktrees: list[AssignedWorktreeResult] = []
    config_result = load_project_config(PROJECT_PATHS.config_file)
    if config_result.config is None:
        if config_result.validation_error is not None:
            summary = summarize_validation_error(config_result.validation_error)
            typer.echo(f"Invalid {PROJECT_PATHS.config_file_display}:\n{summary}", err=True)
        else:
            typer.echo(f"Missing or empty {PROJECT_PATHS.config_file_display}", err=True)
        raise typer.Exit(code=1)

    try:
        ensure_symlink_paths_ignored(config_result.config, PROJECT_PATHS.project_root / ".gitignore")
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error

    if not no_sync:
        try:
            run_git_preflight(continue_requested)
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
            sync_warning = sync_warning_from_exit(error)
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
        return

    output_path = write_output(content)
    typer.echo(f"✅ Onboard context written to: {relative(output_path)}")
    typer.echo(f"📏 Line count: {content.count(chr(10))}")
    typer.echo("")
    typer.echo(
        "NB: YOU MUST read it in full before proceeding. No exceptions, the "
        "document contains important context. An overview or partial reading of "
        "the document is not enough, it must be read in its entirety (every line)."
    )
