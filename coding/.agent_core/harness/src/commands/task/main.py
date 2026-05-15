from __future__ import annotations

import typer

from src.commands.task import amend, complete, list, new, rename, show


app = typer.Typer(help="Manage specification tasks")


app.command("new")(new.run)
app.command("list")(list.run)
app.command("show")(show.run)
app.command("complete")(complete.run)
app.command("amend")(amend.run)
app.command("rename")(rename.run)
