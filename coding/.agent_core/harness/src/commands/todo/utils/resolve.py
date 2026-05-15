import typer

from src.state import todos


def resolve_or_exit(identifier: str) -> str:
    slug, matches = todos.resolve(identifier)
    if slug is not None:
        return slug
    if matches:
        typer.echo(f"Ambiguous todo prefix: {', '.join(matches)}", err=True)
    else:
        typer.echo(f"Todo not found: {identifier}", err=True)
    raise typer.Exit(code=1)
