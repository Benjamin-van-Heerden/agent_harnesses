import typer
from src.commands.promotion import create

app = typer.Typer(help="Advance protected branches through linear promotions")
app.command("create")(create.run)
