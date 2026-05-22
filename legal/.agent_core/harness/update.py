#!/usr/bin/env python3
import deps

deps.require_dependencies()

import typer  # noqa: E402

from src.utils import auto_update  # noqa: E402


def run(
    force: bool = typer.Option(
        False,
        "--force",
        help="Run the updater even when the configured update interval has not elapsed.",
    ),
    reexec: bool = typer.Option(
        False,
        "--reexec",
        help="Re-exec this command after a successful update.",
    ),
) -> None:
    try:
        result = auto_update.update(force=force)
    except auto_update.AutoUpdateError as error:
        typer.echo(f"Harness update failed: {error}", err=True)
        raise typer.Exit(code=1) from error

    if result.skipped_reason:
        typer.echo(f"Harness update skipped: {result.skipped_reason}")
        return

    if not result.updated:
        typer.echo("Harness update not due.")
        return

    typer.echo("Harness update complete.")
    if reexec and result.reexec_required:
        auto_update.reexec_current_command()


if __name__ == "__main__":
    typer.run(run)
