from typing_extensions import Annotated
import typer

from src.commands.docs.utils import run_or_exit
from src.state import optional_docs


def run(
    slugs: Annotated[list[str], typer.Argument(help="Optional doc slugs to install")],
    force: Annotated[bool, typer.Option("--force", help="Overwrite unmanaged files with matching names")] = False,
) -> None:
    run_or_exit(lambda: optional_docs.add(slugs, force=force))
