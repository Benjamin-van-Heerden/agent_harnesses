from pathlib import Path

import typer

from src.config.paths import PROJECT_PATHS
from src.state import logs, specs
from src.state.models import Spec
from src.utils import git


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_PATHS.project_root))
    except ValueError:
        return str(path)


def _active_spec() -> Spec | None:
    branch = git.current_branch()
    if branch is None:
        return None
    for record in specs.list_all():
        if record.branch == branch:
            return record
    return None


def run(spec_slug: str | None = None) -> None:
    active_spec = _active_spec()
    log_spec = specs.get(spec_slug) if spec_slug is not None else active_spec
    effective_spec_slug = log_spec.slug if log_spec else None
    path = logs.create(spec_slug=effective_spec_slug)

    typer.echo(f"Created log file: {_relative(path)}")
    typer.echo("")
    typer.echo(
        "You must read the file and replace every {placeholder} with details from the current interaction session."
    )

    if log_spec is not None:
        typer.echo("")
        typer.echo("If this is the LAST log before completing the spec:")
        typer.echo("  `python .agent_core/harness/main.py spec complete` handles git automatically.")
        typer.echo(
            f'  You must run `python .agent_core/harness/main.py spec complete {log_spec.slug} "detailed commit message"` after editing the log file.'
        )
        typer.echo("")
        typer.echo("Otherwise, you must commit and push your changes:")
        typer.echo("  git add -A && git commit -m '<describe what was done>' && git push")
        return

    typer.echo("")
    typer.echo("You must commit and push your changes:")
    typer.echo("  git add -A && git commit -m '<describe what was done>' && git push")
