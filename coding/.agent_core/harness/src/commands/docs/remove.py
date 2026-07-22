from typing_extensions import Annotated
import typer

from src.commands.docs.utils import run_or_exit
from src.state import optional_docs


def run(
    slugs: Annotated[list[str], typer.Argument(help="Installed optional doc slugs to remove")],
    force: Annotated[bool, typer.Option("--force", help="Remove locally modified managed docs")] = False,
) -> None:
    run_or_exit(lambda: optional_docs.remove(slugs, force=force))
