from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.typst import compile_typst
from src.utils.errors import exit_on_error


app = typer.Typer(help="Compile legal Typst sources")


@app.callback(invoke_without_command=True)
def run(source: Annotated[str | None, typer.Argument()] = None) -> None:
    if source is None:
        typer.echo("Use compile <source.typ>.")
        return
    try:
        output = compile_typst(source)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Compiled Typst source: {source}")
    typer.echo(f"PDF output: {output.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("This is a generated .p.pdf output and should not be committed.")
