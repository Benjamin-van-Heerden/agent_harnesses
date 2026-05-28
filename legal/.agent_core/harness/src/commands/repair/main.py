import tomllib
from datetime import datetime

import typer

from src.config.paths import PROJECT_PATHS
from src.state.logs import recent_global_work_logs
from src.utils.git import run_git


app = typer.Typer(help="Audit legal workspace repair work")
CHECKPOINT_FILE = PROJECT_PATHS.local_context_root / "repair.toml"


def _toml_string(value: str) -> str:
    return (
        '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    )


def _checkpoint_head() -> str:
    if not CHECKPOINT_FILE.is_file():
        return ""
    try:
        data = tomllib.loads(CHECKPOINT_FILE.read_text())
    except tomllib.TOMLDecodeError:
        return ""
    value = data.get("head")
    return value if isinstance(value, str) else ""


def _current_head() -> str:
    result = run_git(PROJECT_PATHS.project_root, ["rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_paths_since(checkpoint: str) -> list[str]:
    paths: set[str] = set()
    if checkpoint:
        result = run_git(
            PROJECT_PATHS.project_root, ["diff", "--name-only", f"{checkpoint}..HEAD"]
        )
        if result.returncode == 0:
            paths.update(
                line.strip() for line in result.stdout.splitlines() if line.strip()
            )
    else:
        result = run_git(PROJECT_PATHS.project_root, ["ls-files"])
        if result.returncode == 0:
            paths.update(
                line.strip() for line in result.stdout.splitlines() if line.strip()
            )

    status = run_git(PROJECT_PATHS.project_root, ["status", "--porcelain"])
    if status.returncode == 0:
        for line in status.stdout.splitlines():
            value = line[3:].strip()
            if " -> " in value:
                value = value.rsplit(" -> ", 1)[1]
            if value:
                paths.add(value)
    return sorted(paths)


def _interesting_paths(paths: list[str]) -> list[str]:
    prefixes = (
        "ZZ_CLIENTS/",
        "UNBOUND/",
        "WIP/",
        "src/",
        "assets/",
        ".praxis/local_context/logs/",
    )
    return [path for path in paths if path.startswith(prefixes)]


def _print_logs() -> None:
    logs = recent_global_work_logs(5)
    if not logs:
        typer.echo("No global work logs found.")
        return
    for record in logs:
        typer.echo(f"- {record.path.relative_to(PROJECT_PATHS.project_root)}")


def _print_instructions(paths: list[str]) -> None:
    typer.echo("Repair instructions")
    typer.echo("-------------------")
    typer.echo(
        "You must inspect the changed legal workspace files listed above before editing."
    )
    typer.echo("Prefer newer clean Typst documents when extracting shared structure.")
    typer.echo("Move reusable visual primitives to src/components/.")
    typer.echo("Move reusable document shells and domain renderers to src/templates/.")
    typer.echo("Move soft domain values and constructors to src/types/.")
    typer.echo(
        "Move constants, theme tokens, firm values, and repeated labels to src/constants/."
    )
    typer.echo("Move reusable static assets to root assets/.")
    typer.echo(
        "Do not preserve local one-off helpers when a shared module is appropriate."
    )
    typer.echo(
        "Do not guess on legally ambiguous chronology, obligation, source-material, or matter-status changes."
    )
    typer.echo(
        "After repair edits, compile changed Typst sources through the harness and run lint."
    )
    if any(path.startswith("UNBOUND/") for path in paths):
        typer.echo(
            "Open unbound matters must remain under UNBOUND/open until bound or closed."
        )


@app.callback(invoke_without_command=True)
def run(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _repair()


def _repair() -> None:
    checkpoint = _checkpoint_head()
    paths = _interesting_paths(_git_paths_since(checkpoint))
    typer.echo("Legal repair")
    typer.echo("============")
    typer.echo(f"Checkpoint: {checkpoint or '(none)'}")
    typer.echo(f"Current HEAD: {_current_head() or '(unavailable)'}")
    typer.echo("")
    typer.echo("Relevant global work logs")
    typer.echo("-------------------------")
    _print_logs()
    typer.echo("")
    typer.echo("Changed practice paths")
    typer.echo("----------------------")
    if paths:
        for path in paths:
            typer.echo(f"- {path}")
    else:
        typer.echo("(no relevant changed practice paths)")
    typer.echo("")
    _print_instructions(paths)


@app.command("checkpoint")
def checkpoint() -> None:
    head = _current_head()
    if not head:
        typer.echo(
            "Cannot create repair checkpoint because git HEAD is unavailable.", err=True
        )
        raise typer.Exit(code=1)
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(
        "\n".join(
            [
                f"head = {_toml_string(head)}",
                f"created_at = {_toml_string(datetime.now().isoformat(timespec='seconds'))}",
                "",
            ]
        )
    )
    typer.echo(
        f"Created repair checkpoint: {CHECKPOINT_FILE.relative_to(PROJECT_PATHS.project_root)}"
    )
    typer.echo("Future repair audits will inspect git changes after this checkpoint.")
