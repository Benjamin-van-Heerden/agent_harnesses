import typer

from src.config.branches import get_branch_names
from src.state import specs
from src.utils import git
from src.utils.errors import GitError
from src.utils import worktrees


app = typer.Typer(help="Clean local git metadata")


@app.command("prune")
def prune() -> None:
    try:
        git.prune()
    except GitError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo("Pruned origin refs.")


@app.command("branch")
def branch(name: str, force: bool = False) -> None:
    protected = set(get_branch_names().protected)
    if name in protected:
        typer.echo(f"Refusing to delete protected branch: {name}", err=True)
        raise typer.Exit(code=1)
    try:
        git.delete_local_branch(name, force=force)
    except GitError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Deleted local branch: {name}")


@app.command("worktrees")
def completed_worktrees(force: bool = False) -> None:
    removed = 0
    for record in specs.list_all(status="completed"):
        if worktrees.remove(record.slug, force=force):
            removed += 1
    typer.echo(f"Removed completed worktrees: {removed}")
