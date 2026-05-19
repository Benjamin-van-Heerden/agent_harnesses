import typer

from src.state import specs
from src.utils import git


def active_spec_slug() -> str:
    branch = git.current_branch()
    if branch is None:
        typer.echo("Could not determine current branch.", err=True)
        raise typer.Exit(code=1)

    for record in specs.list_all():
        if record.branch == branch and record.status in {"todo", "merge_ready"}:
            return record.slug

    typer.echo("No active spec found for the current branch.", err=True)
    typer.echo(
        "Run this command from a spec worktree, or pass the spec slug explicitly.",
        err=True,
    )
    raise typer.Exit(code=1)


def resolve_spec_slug(spec_slug: str | None) -> str:
    if spec_slug is not None:
        return spec_slug
    return active_spec_slug()
