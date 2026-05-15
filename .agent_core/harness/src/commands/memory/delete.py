import typer

from src.commands.memory.utils.resolve import resolve_or_exit
from src.state import memories


def run(identifier: str) -> None:
    slug = resolve_or_exit(identifier)
    memories.delete(slug)
    typer.echo(f"Deleted: {slug}")
