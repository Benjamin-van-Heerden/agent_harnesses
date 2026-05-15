import typer

from src.commands.log import list, new, show


app = typer.Typer(help="Manage work logs")


app.command("new")(new.run)
app.command("list")(list.run)
app.command("show")(show.run)
