---
created_at: '2026-05-13T08:54:19.309461'
username: benjamin_van_heerden
spec_slug: project_local_harness_migration
---
# Work Log - Harness Template Foundation

## Overarching Goals

Continue the `project_local_harness_migration` spec by clarifying the intended
distribution layout and beginning the project-local harness template foundation.
The correct pattern is repository-side templates under `harnesses/mem/`, with an
install payload at `harnesses/mem/.agent_core/harness/`, rather than mutating the
root development CLI in place.

## What Was Accomplished

### Spec Clarification

Updated the spec to explicitly distinguish between:

- repository template root: `harnesses/mem/`
- template-owned runtime payload: `harnesses/mem/.agent_core/harness/`
- installed project runtime: `<project>/.agent_core/harness/`
- installed project-owned state under `<project>/.agent_core/`

The spec now states that implementation should first create and populate
`harnesses/mem/` and migrate runtime code inside that template, while leaving the
root CLI as the development/source command used during migration.

The spec was also updated to state that migrated/refactored harness code should
not use the word `mem` in identifiers, module names, class names, function names,
comments, or new user-facing text unless a specific compatibility surface
requires it. The repository distribution directory remains `harnesses/mem/`.

### Harness Scaffold

Created an initial neutral harness template under `harnesses/mem/`:

- `harnesses/mem/.agent_core/harness/main.py`
- `harnesses/mem/.agent_core/harness/deps.py`
- `harnesses/mem/.agent_core/harness/requirements.txt`
- `harnesses/mem/.agent_core/harness/src/config/paths.py`
- `harnesses/mem/.agent_core/harness/src/config/models.py`
- `harnesses/mem/.agent_core/harness/src/config/main.py`
- `harnesses/mem/AGENTS.md`
- `harnesses/mem/setup.sh`

The scaffold includes:

- a typed `ProjectPaths` model for `.agent_core/`, `.agent_core/harness/`,
  config, user mappings, specs, todos, memories, logs, and docs paths
- neutral config models such as `AgentCoreConfig`, `ProjectConfig`,
  `WorktreeConfig`, and `BranchConfig`
- TOML config loading, validation, unknown-key drift helpers, validation error
  summarization, and default config generation
- a `deps.py` dependency preflight that reports missing Python packages and
  external commands with vanilla `python -m pip install ...` guidance
- a small Typer entrypoint with `paths`, `config show`, and `config default`
  commands to prove the harness foundation is runnable
- a setup script that installs `.agent_core/harness/`, creates state directories,
  creates initial config and user mappings if missing, installs `AGENTS.md`, and
  creates `CLAUDE.md` as a symlink where supported

### Verification

Verified the initial scaffold with focused checks:

- `uv run python harnesses/mem/.agent_core/harness/main.py --help`
- `uv run python harnesses/mem/.agent_core/harness/main.py config default`
- `uvx ruff check` on the new harness Python files
- temp install via `harnesses/mem/setup.sh`
- confirmed setup does not create `.agent_core/tmp/`
- confirmed the new harness code and setup script contain no `mem`, `Mem`, or
  `MEM` occurrences via `rg`

### State Command Consumers

Expanded the harness foundation so actual command consumers use the new
`.agent_core` path layer:

- added frontmatter models for specs, tasks, todos, memories, and logs
- added markdown frontmatter read/write helpers
- added state operation modules for specs, tasks, todos, memories, and logs
- wired basic Typer command families for `spec`, `task`, `todo`, `memory`, and
  `log`

These command families now exercise the neutral `PROJECT_PATHS` object and write
state under `.agent_core/`.

Additional verification:

- focused Ruff check over the full new harness passed
- word-boundary search for the standalone product word in harness code and setup
  returned no matches
- temp install smoke test created a spec, task, todo, memory, and log through
  `python .agent_core/harness/main.py ...`
- the smoke test confirmed no `.mem/` directory and no `.agent_core/tmp/`
  directory were created

### Setup And Update Semantics

Continued into the second task, "Add local harness setup and dependency
preflight".

Improved `harnesses/mem/setup.sh` so setup/update behavior is closer to the spec:

- installs from `harnesses/mem/` into the target project root
- overwrites `.agent_core/harness/` wholesale during install/update
- preserves project-owned state directories and files
- creates `.agent_core/config.toml` when missing
- upserts missing config defaults while preserving existing user values
- preserves `.agent_core/user_mappings.toml`
- creates or refreshes only the managed AGENTS block while preserving user text
- creates `CLAUDE.md` as a symlink on non-Windows systems
- does not create `.agent_core/tmp/`

Added `harnesses/mem/setup_support/upsert_config.py`, a dependency-free setup
helper that can run before harness Python dependencies are installed.

Verified update behavior in a temporary target project:

- existing config values such as custom project name and branch names were
  preserved
- missing config defaults were added
- user mappings were preserved
- project state under `.agent_core/specs/` survived update
- stale files inside `.agent_core/harness/` were removed by update
- existing user content in `AGENTS.md` survived managed block refresh
- `.agent_core/tmp/` was not created

### Onboard And Docs Simplification

Continued into the third task, "Simplify onboard and documentation handling".

Added a harness-local `onboard` command that:

- uses `.agent_core/config.toml`
- reads configured important files
- reads every file under `.agent_core/docs/` recursively in deterministic order
- does not use indexed docs, summaries, vector search, generic templates, or a
  `docs/core/` special case
- includes specs, tasks, open todos, memories, and recent logs from `.agent_core`
  state
- prints to stdout for smaller outputs
- creates `.agent_core/tmp/` lazily only when output is large enough to write to
  a temporary onboard file

Verified onboard in a temporary target project:

- stdout mode included full nested docs content
- state summaries included created spec, task, todo, and memory content
- stdout mode did not create `.agent_core/tmp/`
- large output mode created `.agent_core/tmp/onboard_*.md` lazily
- no `.mem/` directory was created

### Spec Command Subapp

Continued into the fourth task, "Migrate spec command family into a typed
subapp".

Replaced the flat harness spec command module with:

- `src/commands/spec/main.py`
- `src/commands/spec/new.py`
- `src/commands/spec/list.py`
- `src/commands/spec/show.py`
- `src/commands/spec/complete.py`
- `src/commands/spec/abandon.py`
- `src/commands/spec/assign.py`
- `src/commands/spec/models/result.py`
- `src/commands/spec/utils/formatting.py`

The subapp now owns local formatting helpers and a typed command result model.
Basic state-backed behavior is wired through the harness entrypoint:

- `spec new`
- `spec list`
- `spec show`
- `spec complete`
- `spec abandon`

`spec complete` and `spec abandon` now move specs into
`.agent_core/specs/completed/` and `.agent_core/specs/abandoned/` respectively.

`spec assign` is registered but intentionally exits with a "not migrated yet"
message because worktree/GitHub-heavy behavior belongs to the later
sync/GitHub/worktree migration task.

Verified in a temporary target project:

- spec creation, listing, and showing worked
- complete moved the spec into the completed directory
- abandon moved the spec into the abandoned directory
- assign failed explicitly with the not-yet-migrated guard
- focused Ruff check passed
- standalone product-word search still returned no matches in harness code/setup

### Task Command Subapp

Continued into the fifth task, "Migrate task command family into a typed subapp".

Replaced the flat harness task command module with:

- `src/commands/task/main.py`
- `src/commands/task/new.py`
- `src/commands/task/list.py`
- `src/commands/task/show.py`
- `src/commands/task/complete.py`
- `src/commands/task/amend.py`
- `src/commands/task/rename.py`
- `src/commands/task/models/result.py`
- `src/commands/task/utils/formatting.py`

The task subapp owns local formatting helpers and a typed command result model.
Basic state-backed behavior is wired through the harness entrypoint:

- `task new`
- `task list`
- `task show`
- `task complete`
- `task amend`
- `task rename`

Added state helpers for task amendment and rename. `task amend` resets status to
`todo`, clears `completed_at`, updates the timestamp, and appends amendment notes.
`task rename` updates task title and renames the ordered task file while
preserving its numeric prefix.

Verified in a temporary target project:

- created a spec and task
- showed the task
- completed the task with notes
- listed completed tasks
- amended the task back to todo
- renamed the task and verified the old file was removed and the new ordered file
  existed
- focused Ruff check passed

### Todo, Memory, Log, And Report Subapps

Continued into the sixth task, "Migrate todo memory log and report command
families".

Replaced the flat harness command modules for todo, memory, and log with command
family subapps:

- `src/commands/todo/main.py`
- `src/commands/todo/new.py`
- `src/commands/todo/list.py`
- `src/commands/todo/show.py`
- `src/commands/todo/claim.py`
- `src/commands/todo/delete.py`
- `src/commands/todo/utils/formatting.py`
- `src/commands/todo/utils/resolve.py`
- `src/commands/memory/main.py`
- `src/commands/memory/new.py`
- `src/commands/memory/list.py`
- `src/commands/memory/show.py`
- `src/commands/memory/update.py`
- `src/commands/memory/delete.py`
- `src/commands/memory/utils/formatting.py`
- `src/commands/memory/utils/resolve.py`
- `src/commands/log/main.py`
- `src/commands/log/new.py`
- `src/commands/log/list.py`
- `src/commands/log/show.py`
- `src/commands/log/utils/formatting.py`

Added `src/commands/report/main.py` with a weekly report command over
`.agent_core/logs/`.

Verified in a temporary target project:

- created, showed, claimed, and deleted a todo
- created, showed, updated, and deleted a memory
- created, listed, and showed a work log
- generated a weekly report from logs
- confirmed no `.mem/` directory was created
- focused Ruff check passed
- standalone product-word search still returned no matches in harness code/setup

### Sync, GitHub, Worktree, Merge, And Cleanup Migration

Continued into the seventh task, "Migrate sync GitHub worktree merge and cleanup
behavior".

Added neutral shared utility modules:

- `src/utils/errors.py`
- `src/utils/git.py`
- `src/utils/github.py`
- `src/utils/worktrees.py`
- `src/config/branches.py`

These utilities avoid import-time GitHub token checks. `GITHUB_TOKEN` is only
read inside explicit GitHub operations.

Added command subapps:

- `src/commands/sync/main.py`
- `src/commands/worktree/main.py`
- `src/commands/cleanup/main.py`
- `src/commands/merge/main.py`

Migrated behavior:

- `sync status` reports project root, current branch, and dirty state without
  requiring a GitHub token
- `sync branches` performs protected branch fetch/fast-forward sync using config
  branch names
- `sync github-user` performs the explicit GitHub-token-authenticated operation
- `sync issues` synchronizes local specs and todos with GitHub issues using the
  neutral harness labels `spec`, `todo`, and `status:*`
- default `sync` runs issue sync and commits/pushes changed local agent state
- `worktree list/create/remove` wraps local git worktree behavior
- `cleanup prune` prunes origin refs
- `cleanup branch` deletes local branches but refuses configured protected
  branches
- `cleanup worktrees` removes worktrees for completed specs
- `spec assign` now assigns to the authenticated GitHub user, records branch
  metadata, commits/pushes state, creates a worktree, pushes the worktree branch,
  and syncs issue assignment where an issue exists
- `spec complete` validates task completion, commits/pushes/rebases work,
  updates status to `merge_ready`, updates the GitHub issue label, creates a PR,
  records the PR URL, and pushes that metadata
- `merge` merges the recorded PR, marks the spec completed, closes and relabels
  the issue, deletes the remote/local branch, removes the worktree, and
  fast-forwards the dev branch

Verified in a temporary git repository:

- `sync status` worked with `GITHUB_TOKEN` unset
- `sync github-user` failed with actionable `GITHUB_TOKEN` guidance
- `sync issues` failed with actionable `GITHUB_TOKEN` guidance
- cleanup refused to delete the protected `main` branch
- `worktree list` worked
- harness command help imported and listed the migrated sync/worktree/cleanup
  and merge commands
- focused Ruff check passed
- standalone product-word search still returned no matches in harness code/setup

### Removed Surfaces And Template Regression Tests

Continued into the eighth task, "Remove ADR vector docs global config and unused
dependencies".

Added focused harness template tests under `harnesses/mem/tests/` that exercise
the distribution template in temporary projects:

- initial setup creates `.agent_core/harness/`, `config.toml`, and
  `user_mappings.toml`
- setup does not eagerly create `.agent_core/tmp/`
- update preserves project-owned state and existing config values
- update upserts new default config values
- update overwrites stale files inside `.agent_core/harness/`
- onboard reads files under `.agent_core/docs/` recursively without creating
  docs index/vector data
- installed harness commands can create and complete spec tasks, create and
  claim todos, create memories, create logs, and include active project state in
  onboard output
- installed harness local git commands can report sync status without a GitHub
  token, refuse deletion of configured protected branches, create/list/remove a
  real git worktree, and delete the worktree branch after removal
- the root development CLI can perform a one-time `migrate --to-harness`
  upgrade from `.mem/` into `.agent_core/`, preserving old state as `.mem.bak/`
  and omitting removed docs vector/index data
- harness-owned GitHub integration tests clear and recreate the disposable test
  repository named by a single constant, then verify issue sync/import with
  `spec`, `todo`, and `status:*` labels, spec assignment worktree creation,
  spec completion PR creation, and merge cleanup

Also verified the template contains no removed ADR/vector/global-config surfaces
and that the migrated/refactored harness code still avoids the standalone
product word.

Focused verification passed:

- `uv run pytest harnesses/mem/tests/test_setup.py
  harnesses/mem/tests/test_onboard.py
  harnesses/mem/tests/test_local_commands.py
  harnesses/mem/tests/test_worktrees.py
  harnesses/mem/tests/test_migration.py -v`
- `uv run pytest harnesses/mem/tests/test_github_flow.py -v`
- `uvx ruff check harnesses/mem/.agent_core/harness
  harnesses/mem/setup_support/upsert_config.py
  harnesses/mem/tests src/commands/migrate.py src/utils/migrate.py`
- standalone product-word scan over harness code, setup, and setup support
- removed-surface scan for ADRs, vector/index dependencies, global config, and
  docs search/index command text
- `find harnesses/mem -name __pycache__ -o -name '*.pyc'`

Attempted a full `uv run pytest -v` run. The harness-local tests passed at the
start of the run. The broader root CLI/GitHub integration suite is not clean in
the current test environment:

- `tests/test_init.py` fails because `init()` prompts for branch names while
  pytest has stdin captured.
- `tests/test_github_sync.py::test_spec_outbound_sync` fails in isolation
  because the copied GitHub test repo already contains an
  `outbound_sync_test` spec with an issue id, causing `spec new` to create a
  suffixed slug.
- A full run later hung in a GitHub push during an integration test and was
  stopped.

## Key Files Affected

- `.mem/specs/project_local_harness_migration/spec.md` - clarified the
  repository-template vs installed-project layout and added the no-`mem` naming
  constraint for migrated/refactored harness code.
- `harnesses/mem/.agent_core/harness/deps.py` - added dependency preflight.
- `harnesses/mem/.agent_core/harness/main.py` - added initial neutral Typer
  entrypoint.
- `harnesses/mem/.agent_core/harness/requirements.txt` - added initial retained
  runtime dependencies.
- `harnesses/mem/.agent_core/harness/src/config/paths.py` - added typed
  project/harness path model.
- `harnesses/mem/.agent_core/harness/src/config/models.py` - added typed config
  models.
- `harnesses/mem/.agent_core/harness/src/config/main.py` - added TOML config
  loading, validation, drift helpers, and default config generation.
- `harnesses/mem/.agent_core/harness/src/models/frontmatter.py` - added typed
  frontmatter models for state files.
- `harnesses/mem/.agent_core/harness/src/utils/markdown.py` - added markdown
  frontmatter parsing and writing helpers.
- `harnesses/mem/.agent_core/harness/src/state/` - added state operation modules
  for specs, tasks, todos, memories, and logs.
- `harnesses/mem/.agent_core/harness/src/commands/` - added basic command
  consumers for specs, tasks, todos, memories, and logs.
- `harnesses/mem/.agent_core/harness/src/commands/onboard.py` - added simplified
  full-read onboard behavior.
- `harnesses/mem/.agent_core/harness/src/commands/spec/` - migrated spec command
  behavior into a subapp with local modules, models, and formatting helpers.
- `harnesses/mem/.agent_core/harness/src/commands/task/` - migrated task command
  behavior into a subapp with local modules, models, and formatting helpers.
- `harnesses/mem/.agent_core/harness/src/commands/todo/` - migrated todo command
  behavior into a subapp with local helpers.
- `harnesses/mem/.agent_core/harness/src/commands/memory/` - migrated memory
  command behavior into a subapp with local helpers.
- `harnesses/mem/.agent_core/harness/src/commands/log/` - migrated log command
  behavior into a subapp with local helpers.
- `harnesses/mem/.agent_core/harness/src/commands/report/` - added weekly report
  command behavior over local logs.
- `harnesses/mem/.agent_core/harness/src/utils/git.py` - added neutral git
  helpers.
- `harnesses/mem/.agent_core/harness/src/utils/github.py` - added explicit
  GitHub-token-authenticated helpers.
- `harnesses/mem/.agent_core/harness/src/utils/worktrees.py` - added neutral
  worktree helpers.
- `harnesses/mem/.agent_core/harness/src/commands/sync/` - added sync status,
  branch sync, and explicit GitHub user command.
- `harnesses/mem/.agent_core/harness/src/commands/worktree/` - added worktree
  list/create/remove commands.
- `harnesses/mem/.agent_core/harness/src/commands/cleanup/` - added prune and
  protected-branch-safe local branch cleanup commands.
- `harnesses/mem/.agent_core/harness/src/commands/merge/` - registered a guarded
  PR merge command.
- `harnesses/mem/.agent_core/harness/src/state/specs.py` - updated status
  transitions to move completed and abandoned specs into subdirectories.
- `harnesses/mem/.agent_core/harness/src/state/tasks.py` - added amend and rename
  state operations.
- `harnesses/mem/AGENTS.md` - added local harness usage instructions.
- `harnesses/mem/setup.sh` - added initial install/update script.
- `harnesses/mem/setup_support/upsert_config.py` - added dependency-free setup
  helper for config creation and conservative default upsert.
- `harnesses/mem/tests/` - added focused regression tests for template
  setup/update semantics, simplified docs onboarding, installed harness command
  smoke coverage, local worktree behavior, removed-surface absence, one-time
  original-state migration into the project-local harness layout, and
  harness-owned GitHub integration flows.
- `src/commands/migrate.py` - added `--to-harness` migration mode.
- `src/utils/migrate.py` - added the original `.mem/` to `.agent_core/`
  compatibility migration implementation.

## Errors and Barriers

An initial attempt incorrectly modified the existing root runtime directly
instead of starting from the repository-side harness template. The user rejected
that approach, and the worktree was reset with `git reset --hard HEAD` and
`git clean -fd` before restarting. Do not repeat that in the next session:
migration work should happen under `harnesses/mem/.agent_core/harness/` unless a
root development file must be changed to support or verify the template.

The first setup smoke test also exposed that `setup.sh` tried to generate
`config.toml` by running the harness before dependencies were installed. That
was corrected by writing the initial config directly from shell during setup.

## What Comes Next

Seven spec tasks have been marked complete. The final task, "Remove ADR vector
docs global config and unused dependencies", has focused regression coverage and
verification passing, but has not been marked complete yet because it still needs
explicit user approval.

Recommended next steps:

1. Review the final cleanup/dependency, migration, local command, worktree, and
   GitHub integration coverage in `harnesses/mem/tests/`.
2. Review the full diff for the spec before deciding whether to complete the
   spec.
3. Decide whether to fix the existing root CLI/GitHub integration test
   reliability issues before completing the spec, or record them as residual
   test-environment risk.
4. Keep the root CLI intact unless a change is explicitly needed to support
   generating, testing, or distributing the template.
