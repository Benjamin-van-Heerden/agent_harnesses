import typer
from src.commands.pr import actions, merge, review

app = typer.Typer(help="Discover, review, respond to, and merge pull requests")
app.command("review")(review.run)
app.command("comment")(actions.comment)
app.command("approve")(actions.approve)
app.command("request-changes")(actions.request_changes)
app.command("merge")(merge.run)
