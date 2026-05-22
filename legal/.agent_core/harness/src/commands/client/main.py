from typing import Annotated

import typer

from src.config.paths import PROJECT_PATHS
from src.state.clients import create_client, list_clients
from src.utils.errors import exit_on_error


app = typer.Typer(help="Manage legal clients")


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("Use a client subcommand.")


@app.command("list")
def list_command() -> None:
    clients = list_clients()
    typer.echo("slug\tdisplay_name\tclient_type\topen_matters\tresolved_matters")
    if not clients:
        typer.echo("(no clients yet)")
        return
    for client in clients:
        client_dir = client.path.parent
        open_dir = client_dir / "matters" / "open"
        resolved_dir = client_dir / "matters" / "resolved"
        open_count = sum(1 for path in open_dir.iterdir() if path.is_dir()) if open_dir.is_dir() else 0
        resolved_count = sum(1 for path in resolved_dir.iterdir() if path.is_dir()) if resolved_dir.is_dir() else 0
        typer.echo(
            f"{client.client_slug}\t{client.display_name}\t{client.client_type}\t{open_count}\t{resolved_count}"
        )


@app.command("new")
def new_command(
    slug: Annotated[str, typer.Argument()],
    display_name: Annotated[str, typer.Argument()],
    client_type: Annotated[str, typer.Argument()],
) -> None:
    try:
        profile = create_client(slug, display_name, client_type)
    except (FileExistsError, ValueError) as error:
        exit_on_error(error)

    typer.echo(f"Created client: {slug} ({display_name})")
    typer.echo(f"Profile: {profile.relative_to(PROJECT_PATHS.project_root)}")
    typer.echo("You must review the client profile and fill in contact, billing, and conflict details before substantive work.")
