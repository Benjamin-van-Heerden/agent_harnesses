from __future__ import annotations

import typer

from src.commands.spec import abandon, assign, complete, list, new, show


app = typer.Typer(help="Manage specifications")


app.command("new")(new.run)
app.command("list")(list.run)
app.command("show")(show.run)
app.command("complete")(complete.run)
app.command("abandon")(abandon.run)
app.command("assign")(assign.run)
