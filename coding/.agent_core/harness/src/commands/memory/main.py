import typer

from src.commands.memory import delete, list, new, show, update


app = typer.Typer(help="Manage project memories")


app.command("new")(new.run)
app.command("list")(list.run)
app.command("show")(show.run)
app.command("update")(update.run)
app.command("delete")(delete.run)
