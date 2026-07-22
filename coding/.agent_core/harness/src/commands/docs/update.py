from typing_extensions import Annotated
import typer

from src.commands.docs.utils import run_or_exit
from src.state import optional_docs


def run(
    slugs: Annotated[list[str] | None, typer.Argument(help="Installed optional doc slugs to update")] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite locally modified managed docs")] = False,
) -> None:
    run_or_exit(lambda: optional_docs.update(slugs or [], force=force))
