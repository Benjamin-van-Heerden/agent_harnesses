# Harness Structure

`coding/` is the reference shape for project-native harnesses. Other harnesses do not need to copy its coding-specific workflow concepts, but they should follow the same installation model, runtime layout, command composition pattern, and agent-facing stdout behavior.

This document is descriptive guidance. It explains how native harnesses are expected to fit together so future harnesses feel consistent and can be installed, updated, and operated the same way.

## Core Model

A native harness has three main surfaces:

- `AGENTS.md`: the agent entrypoint and workflow contract.
- `setup.sh`: the installer and updater for any target project directory.
- `.agent_core/harness/`: the project-local Python runtime that implements the CLI commands.

The installed project also has a root-level `.agent_core/` directory that holds project-owned state. That root-level state is not where harness development happens. Harness implementation changes belong in the harness template itself, for example `coding/.agent_core/harness/`, then get propagated by `setup.sh`.

## AGENTS.md

`AGENTS.md` is the first-class entrypoint for the agent. It should explain the workflow the agent is expected to follow, including:

- the first command to run when starting a session;
- which local Python invocation to use for harness commands;
- the concepts the harness exposes;
- commands the agent is expected to know about;
- hard rules around sequencing, permissions, and stopping points.

The file may intentionally expose only part of the harness capability surface. That is acceptable. Some commands or workflows may be obscured to force agents through a safer or more deliberate path.

The installed `AGENTS.md` should contain a managed core block from the harness template. If an installed project already has an `AGENTS.md`, setup should update the managed block without deleting project-specific notes outside that block.

## setup.sh

`setup.sh` installs the harness into the current working directory. It should be possible to run it from any chosen target project directory.

In the reference harness, setup does the following:

- resolves the harness template locally or by cloning the harness repository;
- creates required project state directories under `.agent_core/`;
- creates or updates `.agent_core/config.toml` without clobbering existing
  project choices;
- validates required repository assumptions, such as protected branches;
- replaces `.agent_core/harness/` with the template runtime;
- creates durable support files such as `.agent_core/user_mappings.toml` when
  needed;
- installs or updates the managed block in `AGENTS.md`;
- manages compatibility files, such as `CLAUDE.md` linking to `AGENTS.md`;
- exposes optional documentation commands such as `setup.sh docs list`, `setup.sh docs add`, and `setup.sh docs update`.

The important split is that setup may replace the managed runtime, but it must preserve project-owned state. A `setup.sh --update` should refresh the harness implementation without deleting specs, todos, memories, logs, docs, config, or other durable project data.

## Installed .agent_core

The installed root `.agent_core/` belongs to the target project. Its exact shape depends on the harness, but the boundary should stay clear:

- `.agent_core/harness/` is managed runtime code and may be overwritten by setup.
- `.agent_core/config.toml` is durable project configuration.
- `.agent_core/docs/` is durable project context included by onboard-style flows.
- other state directories are harness-specific durable state.

For the coding harness, durable state includes:

- `.agent_core/specs/`
- `.agent_core/todos/`
- `.agent_core/memories/`
- `.agent_core/logs/`
- `.agent_core/docs/`
- `.agent_core/user_mappings.toml`

Other harnesses can choose different state concepts, but should keep the same separation between managed runtime and project-owned data.

## Runtime Layout

The Python runtime layout used by `coding/` should be treated as canonical for native harnesses:

```text
.agent_core/harness/
  main.py
  deps.py
  requirements.txt
  src/
    commands/
    config/
    models/
    state/
    utils/
```

`main.py` is the CLI composition root. It should stay small. Its job is to:

- require dependencies before importing the command graph;
- create the root `typer.Typer` app;
- import command-group apps;
- register those command groups with `app.add_typer`;
- keep only truly top-level commands inline.

The reference pattern is:

```python
import deps

deps.require_dependencies()

import typer

from src.commands.example.main import app as example_app

app = typer.Typer(help="Project-local agent harness")
app.add_typer(example_app, name="example")

if __name__ == "__main__":
    app()
```

## Commands

Commands should be split by workflow area under `src/commands/`. Each command group gets a `main.py` that owns the Typer sub-app and registers individual command files.

The reference shape is:

```text
src/commands/
  task/
    main.py
    new.py
    list.py
    show.py
    complete.py
```

`task/main.py` should be mostly wiring:

```python
import typer

from src.commands.task import complete, list, new, show

app = typer.Typer(help="Manage tasks")
app.command("new")(new.run)
app.command("list")(list.run)
app.command("show")(show.run)
app.command("complete")(complete.run)
```

Each command file should expose a focused `run(...)` function. The command file should handle user-facing CLI behavior: argument definitions, error conversion to `typer.Exit`, and stdout/stderr messages. Shared business logic should live in `state/` or `utils/` rather than being duplicated across commands.

This split keeps command registration obvious, makes command files small, and lets future harnesses add or remove workflow areas without turning `main.py` into a large command implementation file.

## stdout As Agent Guidance

Harness stdout is part of the control surface. It is not just status reporting. Commands should print clear instructions that guide the agent's next action.

Good stdout tells the agent:

- what changed;
- what file or path matters next;
- whether the command is complete or intentionally blocked;
- what command must be run next, when there is a required next step;
- what the agent must read before proceeding;
- why the harness refused to continue.

Examples from the reference harness include:

- `onboard` prints the full context or writes it to a temp file and explicitly tells the agent it must read that file before proceeding.
- `log new` creates a log file and tells the agent to replace every placeholder, then either complete the spec or commit and push.
- `spec complete` refuses to proceed with incomplete tasks and lists the tasks.
- cleanup commands refuse protected branch deletion and say which branch was protected.

Use assertive, authoritative phrasing. Prefer "You must ..." for required agent actions. Avoid deferential phrasing when the harness is enforcing workflow.

## Config And Paths

Harnesses should centralize project paths and config parsing.

The reference layout separates this into:

- `src/config/paths.py`: resolves project root, state root, harness root, config file, and state directories from the current working directory.
- `src/config/models.py`: typed config models.
- `src/config/main.py`: TOML loading, validation, drift detection, and default config generation.

Commands should not hard-code scattered `.agent_core/...` paths. They should use central path helpers so worktrees, setup-installed projects, and future harnesses all resolve paths consistently.

## State

State should be file-first and typed.

The reference harness stores durable records as markdown files with YAML frontmatter and parses them into explicit Pydantic models. Command code works with typed records rather than raw dictionaries.

The specific state concepts are harness-specific. A coding harness may have specs, tasks, todos, memories, and logs. Another harness may have different records. The structural principle stays the same:

- state lives under the installed root `.agent_core/`;
- file formats are readable and git-native;
- loaders parse files into typed records;
- command code calls state APIs instead of manipulating files ad hoc.

## Utilities

Reusable integrations and side-effect helpers belong under `src/utils/`.

In the reference harness this includes Git, GitHub, worktree, markdown, and error helpers. Other harnesses should follow the same pattern: commands orchestrate, state modules read and write durable state, and utils wrap external systems.

## Dependencies

`deps.py` should check required Python packages and external commands before the Typer app imports command modules. This gives the agent a direct installation message instead of a Python traceback.

The dependency message should include the exact packages or commands needed.

## Optional Docs

Optional docs live in the harness template, outside the installed project state, and are copied into `.agent_core/docs/` only when requested.

This lets a harness provide reusable guidance, such as language or framework notes, without forcing every project to carry every optional document.

## Development And Updates

Harness implementation work should happen in the harness template directory, not inside an installed project's root `.agent_core/` runtime. For the coding harness, that means editing files under `coding/`, especially `coding/.agent_core/harness/`.

The expected update loop for the coding harness is:

```bash
# make changes under coding/
git push
bash <(curl -sL https://raw.githubusercontent.com/Benjamin-van-Heerden/agent_harnesses/main/coding/setup.sh) --update
```

That loop keeps the installed runtime disposable and makes the template the source of truth.
