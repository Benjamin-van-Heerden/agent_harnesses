import typer

from src.utils import worktrees
from src.utils.errors import GitError


app = typer.Typer(help="Manage local worktrees")


@app.command("list")
def list_items() -> None:
    try:
        records = worktrees.list_all()
    except GitError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    for record in records:
        marker = "main" if record.is_main else "worktree"
        typer.echo(f"- [{marker}] {record.branch}: {record.path}")


@app.command("create")
def create(slug: str, branch: str) -> None:
    try:
        path = worktrees.create(slug, branch)
    except GitError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Created: {path}")


@app.command("remove")
def remove(slug: str, force: bool = False) -> None:
    try:
        removed = worktrees.remove(slug, force=force)
    except GitError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    if removed:
        typer.echo(f"Removed: {slug}")
    else:
        typer.echo(f"No worktree found for: {slug}")
