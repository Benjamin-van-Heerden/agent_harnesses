from __future__ import annotations

import typer

from src.commands.todo import claim, delete, list, new, show


app = typer.Typer(help="Manage standalone todos")


app.command("new")(new.run)
app.command("list")(list.run)
app.command("show")(show.run)
app.command("claim")(claim.run)
app.command("delete")(delete.run)
