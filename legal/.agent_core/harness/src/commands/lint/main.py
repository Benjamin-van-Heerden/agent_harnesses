import typer

from src.state.lint import lint_frontmatter


app = typer.Typer(help="Check legal harness state")


@app.callback(invoke_without_command=True)
def run() -> None:
    errors = lint_frontmatter()
    if not errors:
        typer.echo("all frontmatter valid")
        return
    for error in errors:
        typer.echo(error)
    typer.echo("")
    typer.echo(f"{len(errors)} issue(s) found")
    raise typer.Exit(code=1)
