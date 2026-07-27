import typer

from src.commands.docs import add, list, remove, update


app = typer.Typer(help="Manage optional project documentation")


app.command("list")(list.run)
app.command("add")(add.run)
app.command("remove")(remove.run)
app.command("update")(update.run)
