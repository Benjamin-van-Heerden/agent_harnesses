---
title: Project-local harness migration
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 104
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/104
branch: dev-benjamin_van_heerden-project_local_harness_migration
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/105
created_at: '2026-05-12T16:22:04.370880'
updated_at: '2026-05-15T11:21:59.938775'
completed_at: '2026-05-15T11:21:59.937115'
last_synced_at: '2026-05-15T11:14:15.010850'
local_content_hash: 0781842dca78c1559c329715810e315fac35c879a4d7b3334cdb60fd937791e1
remote_content_hash: 0781842dca78c1559c329715810e315fac35c879a4d7b3334cdb60fd937791e1
---
## Overview

Convert the current globally-installed CLI model into a project-local full harness.

Today the tool assumes it exists somewhere on the caller's machine and is exported on `PATH`, with local state in `.mem/` and some runtime/config assumptions leaking through `~/.config/mem`. That makes distribution fragile. The target model is closer to mem-lite/Praxis installation, but without losing the full feature set: each project installs a local `.agent_core/` directory that contains both the managed runtime harness and the project-owned state.

The installed project should look broadly like:

```text
my_project/
  .agent_core/
    harness/
      main.py
      deps.py
      src/
        commands/
          spec/
            main.py
            models/
            utils/
            new.py
            complete.py
            assign.py
          task/
            main.py
            models/
            utils/
          todo/
            main.py
            models/
            utils/
          ...
        models/
        utils/
    docs/
    logs/
    memories/
    specs/
    todos/
    config.toml
    user_mappings.toml
  AGENTS.md
  CLAUDE.md
```

The harness is fully managed and may be overwritten wholesale by `setup.sh --update`. Project state and user-owned configuration must be preserved or schema-upserted.

The repository-side distribution template and the installed project layout are distinct:

- Repository template root: `harnesses/mem/`.
- Template-owned install payload: `harnesses/mem/.agent_core/harness/`.
- Template-owned project files: `harnesses/mem/AGENTS.md` and `harnesses/mem/setup.sh`.
- Installed project root: the target user's repository.
- Installed runtime: `<project>/.agent_core/harness/`.
- Installed project-owned state: `<project>/.agent_core/{config.toml,user_mappings.toml,specs,tasks,todos,memories,logs,docs}`.

Implementation should first create/populate the `harnesses/mem/` template and migrate the runtime code inside `harnesses/mem/.agent_core/harness/`. Do not start by rewriting the root development CLI in place; the root CLI remains the development/source command used to build and verify the template during migration.

The migration should start from the current path/config foundation (`env_settings.py`) because all later command behavior depends on correctly defining:

- where the installed harness lives,
- where project-owned state lives,
- where commands are invoked from,
- which files are managed vs user-owned,
- and which assumptions about global install/config are no longer valid.

## Goals

- Install the full runtime into each project so agents can run it with vanilla Python, without requiring a global CLI on `PATH`.
- Replace `.mem/` project state with `.agent_core/` project state.
- Remove dependence on `~/.config/mem`; all necessary runtime/configuration should be local to the project.
- Rename/rework `env_settings.py` into a clearer project-local configuration/path module or package. Prefer neutral names such as `config`/`settings`/`paths`; avoid unnecessary self-reference in new code.
- Reorganize commands from flat `src/commands/*.py` files into command-family subapps:
  - each subapp has `main.py`,
  - each subapp has `models/`,
  - subapp-local helpers stay under that subapp's `utils/`,
  - shared models live under `src/models/`,
  - shared helpers live under `src/utils/`.
- Use more typed models, not fewer. Prefer Pydantic/dataclass models for structured command/config/state data instead of ad hoc dictionaries.
- Add a local `setup.sh` distribution flow similar to Praxis:
  - init creates `.agent_core/`, `AGENTS.md`, and `CLAUDE.md`,
  - update fully overwrites `.agent_core/harness/`,
  - update upserts structured config defaults while preserving user values,
  - update preserves project-owned state.
- Use vanilla Python invocation for installed projects, e.g. `python .agent_core/harness/main.py onboard`.
- Add `deps.py` preflight before the Typer app starts. It should check required Python packages and external commands and print actionable installation guidance when something is missing.
- Remove ADR functionality.
- Remove vector-search/indexed documentation functionality and its dependencies.
- Simplify docs: no `docs/core/`; everything in `.agent_core/docs/` is read in full during onboard.
- Do not create `.agent_core/tmp/` during setup. Commands that need temporary files should create temporary directories/files only when needed.

## Technical Approach

Proceed in a foundation-first, command-by-command migration. Avoid broad speculative rewrites. Each step should leave the app in a runnable state where possible.

### 1. Path and Config Foundation

Replace the current `env_settings.py` concept with a project-local configuration/path layer.

Current problems to eliminate:

- `ENV_SETTINGS.mem_working_dir` assumes a separate source repo/runtime location.
- `ENV_SETTINGS.mem_dir` points at `.mem`.
- `ENV_SETTINGS.global_config_dir` and `global_config_file` point at `~/.config/mem`.
- path string helpers hard-code `.mem/...`.
- `get_env_settings()` asserts `GITHUB_TOKEN` at import time, which makes non-GitHub commands depend on GitHub configuration too early.

Target behavior:

- Commands derive the project root from the invocation cwd.
- State root is `.agent_core/`.
- Runtime root is `.agent_core/harness/`.
- Config file is `.agent_core/config.toml`.
- User mappings file is `.agent_core/user_mappings.toml`.
- Specs, tasks, todos, memories, logs, and docs live under `.agent_core/`.
- No global config directory is consulted.
- GitHub token validation happens only when a GitHub operation actually needs it.

The new config/path layer inside the harness template should expose typed path/settings objects. If a package is warranted, use something like:

```text
harnesses/mem/.agent_core/harness/src/config/
  main.py       # load/upsert project config
  models.py     # typed config schema
  paths.py      # project/harness path model
```

### 2. Local Harness Packaging and Setup

Add a new installable harness template under a distribution path such as:

```text
harnesses/
  mem/
    .agent_core/
      harness/
        main.py
        deps.py
        src/
        requirements.txt
    AGENTS.md
    setup.sh
  ...more-harnesses-here-in-the-future/
```

The distribution template path is `harnesses/mem/`. When installed into a target project, the installed project path should be `.agent_core/`.

Existing projects using the original `.mem/` layout need a one-time upgrade path
from the root development CLI. The migration should install the
`harnesses/mem/` template into the target project, copy project-owned state into
`.agent_core/`, rewrite config to the harness schema, skip removed docs
vector/index data, refresh the managed AGENTS block, and preserve the old
`.mem/` directory as `.mem.bak/` for rollback. References to the legacy product
name and `.mem/` path are allowed only inside this compatibility migration
surface.

`setup.sh` policies:

- `init`: install from `harnesses/mem/` into the target project root, create `.agent_core/` state directories, copy the managed harness to `.agent_core/harness/`, create config/user mappings if missing, create/refresh managed AGENTS block.
- `--update`: overwrite `.agent_core/harness/` fully.
- `--update`: upsert `.agent_core/config.toml` defaults into existing config while preserving existing user values.
- `--update`: preserve `.agent_core/user_mappings.toml` values and add missing structure only if needed.
- `--update`: preserve specs, tasks, todos, memories, logs, and user docs.
- `--update`: refresh only explicitly managed docs if managed docs are introduced; user docs must remain preserved.
- `CLAUDE.md`: symlink to `AGENTS.md` where safe, copy on Windows, following the Praxis pattern.

No `tmp/` directory should be created by setup.

### 3. Dependency Preflight

Add `deps.py` at the harness entrypoint level. It runs before Typer app registration/execution.

It should:

- check importability of required Python packages,
- check required external commands only when they are globally required,
- avoid importing heavy command modules before dependency checks complete,
- print clear install guidance using vanilla Python/pip style, not `uv`,
- exit cleanly if dependencies are missing.

As the docs/vector-search functionality is removed, dependencies such as ChromaDB, Agno, OpenAI, Voyage, Unstructured, Textual, and Markdown should be removed unless still needed by retained functionality.

### 4. Command Subapp Migration

Move one command family at a time from flat modules into subapps. Each command family should own its local models and utilities.

Target pattern:

```text
harnesses/mem/.agent_core/harness/src/commands/spec/
  main.py
  models/
  utils/
  new.py
  list.py
  show.py
  assign.py
  complete.py
  abandon.py
```

Shared cross-subapp models go in `harnesses/mem/.agent_core/harness/src/models/`; shared helpers go in `harnesses/mem/.agent_core/harness/src/utils/`.

Do not promote helpers to shared locations until at least two subapps actually need them.

Suggested migration order:

1. foundation/config/path layer,
2. onboard/docs simplification,
3. spec command family,
4. task command family,
5. todo command family,
6. memory command family,
7. log/report command family,
8. sync/GitHub/worktree command family,
9. merge/cleanup command family,
10. init/patch/setup-related commands,
11. remove ADR/docs-index/introspect surfaces and unused dependencies.

### 5. Onboard Simplification

Onboard should:

- use `.agent_core/config.toml`,
- sync where appropriate using local command code,
- read every file under `.agent_core/docs/` in full,
- not distinguish `docs/core/`,
- not use semantic/vector search,
- not load generic templates from global config,
- refer to local invocation commands in output, e.g. `python .agent_core/harness/main.py ...`.

### 6. Naming and Self-Reference

Migrated/refactored harness code should avoid product self-reference. Do not use the word `mem` in new or migrated code identifiers, module names, class names, function names, comments, or new user-facing text unless a specific compatibility surface requires it. The repository distribution directory remains `harnesses/mem/`, but the code inside the harness should use neutral domain names.

Prefer neutral domain names such as:

- `AgentCoreConfig` or `ProjectConfig` instead of `MemLocalConfig`,
- `STATE_ROOT`/`agent_core_dir` instead of `mem_dir`,
- `project_root` instead of `caller_dir`,
- `harness_root` instead of `mem_working_dir`.

Installed-project command examples should use `python .agent_core/harness/main.py ...`, not a global `mem` command.

## Success Criteria

- A fresh project can install the local harness with `setup.sh` and run onboarding with vanilla Python.
- Installed-project instructions do not require a global CLI on `PATH`.
- `.agent_core/harness/` can be deleted and restored by `setup.sh --update` without losing project state.
- `.agent_core/config.toml` update behavior is an upsert: missing default keys are added, existing user values are preserved.
- No command reads from or writes to `~/.config/mem`.
- No command uses `.mem/` as the active state root after migration.
- ADR commands, ADR templates, and ADR utilities are removed.
- Docs index/search/summarization commands and vector-search dependencies are removed.
- Onboard reads `.agent_core/docs/` files in full.
- Command families are organized as subapps with local `models/` and `utils/` folders where useful.
- Shared models/helpers are only placed in global `src/models/` and `src/utils/` when used by more than one command family.
- Tests or focused verification cover the migrated command families and setup/update config behavior.

## Notes

- The current repo still uses `uv` for development commands per existing project rules. The installed harness target should not require `uv`.
- During development of this repo, prefer `uv run python main.py ...` over invoking the globally installed CLI, per existing AGENTS instructions.
- Do not assign this spec until the body and tasks are complete and synced. After assignment, implementation should happen in the created worktree and a new agent session should start there.
- Be careful with update semantics. `harness/` is disposable and managed; project state is not.
