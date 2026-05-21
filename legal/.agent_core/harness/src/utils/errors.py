from typing import NoReturn

import typer


class HarnessError(Exception):
    pass


def fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def exit_on_error(error: Exception) -> NoReturn:
    fail(str(error))
