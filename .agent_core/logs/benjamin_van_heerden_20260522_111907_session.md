---
created_at: '2026-05-22T11:19:07.272057'
username: benjamin_van_heerden
---
Work Log - Mission Control Todo Guards And Cache Cleanup

## Overarching Goals

Tighten the coding harness around the intended branch roles: `dev` is mission control for project management, non-`dev` non-spec branches should not advertise or allow spec/todo management actions, spec worktree onboarding should make its automatic `origin/dev` rebase behavior explicit, and generated Python cache artifacts must not be installed or retained as managed harness files.

## What Was Accomplished

### Confirmed spec worktree rebase behavior

Inspected the active legal migration spec worktree branch relationship. The spec branch merge base matched current `origin/dev`, confirming the branch was already rebased onto latest `origin/dev`. The surprising `git diff dev-benjamin_van_heerden-migrate_legal_harness_to_native_agent_core_structure --stat` output was explained as a likely checkout/context issue: running `git diff <spec-branch>` from the main `dev` checkout compares the main working tree to the spec branch, so spec-only files appear as deletions.

### Restricted todo mutations to mission control

Added a shared todo command context guard that requires mutating todo commands to run from the main repository on the configured `dev` branch. The guard rejects worktrees, detached HEAD, and non-`dev` branches with direct recovery guidance.

Applied the guard to:

- `todo new`
- `todo claim`
- `todo delete`

Read-only todo commands remain available from any branch.

### Updated onboard guidance

Updated onboard content so spec and todo management commands only appear when no spec is active and the current branch is configured `dev`. Non-`dev` non-spec branches now receive guidance that they are outside the normal mission control workflow and should switch back to `dev` for spec/todo management unless the user deliberately chooses exceptional ad hoc work.

Strengthened mission-control wording on `dev` to frame it as the control plane for ad hoc edits, specs, todos, merges, and project state inspection.

### Made spec worktree rebase visible

Changed spec worktree sync so successful `dev-*` worktree sync prints that the branch was rebased onto `origin/dev` and pushed with `--force-with-lease`.

Aligned sync dirtiness checks with onboard preflight by blocking all uncommitted changes before sync/rebase, not just tracked changes.

### Removed Python cache artifacts from managed harness updates

Updated the coding setup installer so managed harness sync excludes any source path under `__pycache__` and any `.pyc` file. Setup now also actively removes Python cache directories and stray `.pyc` files from the installed `.agent_core/harness` target if they are found.

Updated auto-update so it also removes Python cache artifacts from the installed harness before deciding whether a remote update is skipped or run. This means cache cleanup still happens when auto-update is skipped because it is not due, disabled, running from a worktree, or on a non-dev branch.

Reran `python -B coding/setup.py --update` to propagate the auto-update cleanup behavior into the project-local installed runtime and confirmed there are no `__pycache__` directories or `.pyc` files under either `coding/.agent_core/harness` or `.agent_core/harness`.

### Renamed the managed AGENTS block tags

Changed the coding harness template `AGENTS.md` managed block tags from `<AGENT_CORE>` / `</AGENT_CORE>` to `<core_instructions>` / `</core_instructions>`.

Updated `coding/setup.py` to use the new tag names for future installs and updates while still detecting and replacing existing legacy `<AGENT_CORE>` blocks. Reran `python -B coding/setup.py --update` so the repository root `AGENTS.md` was migrated to the new tags.

### Moved shared listing helpers to global utils

Moved the shared list-command table and date formatting helpers from `src/commands/utils/listing.py` to `src/utils/listing.py`. Updated log, memory, spec, task, and todo list commands to import from the global utility module.

Reran `python -B coding/setup.py --update` so the installed project-local runtime created `.agent_core/harness/src/utils/listing.py` and removed the stale `.agent_core/harness/src/commands/utils/listing.py`.

### Verification

Verification completed:

- `uvx ruff check` on edited harness and test files.
- `uv run ty check` on edited harness and test files.
- `uv run pytest coding/tests/test_todo_context.py`
- `uv run pytest coding/tests/test_git_sync.py -k sync_git_state`
- `uv run pytest coding/tests/test_onboard.py -k non_dev_branch`
- `uvx ruff check coding/setup.py coding/.agent_core/harness/src/utils/auto_update.py coding/tests/test_setup.py coding/tests/test_auto_update.py`
- `uv run ty check coding/setup.py coding/.agent_core/harness/src/utils/auto_update.py coding/tests/test_setup.py coding/tests/test_auto_update.py`
- `uv run pytest coding/tests/test_setup.py -k python_cache coding/tests/test_auto_update.py`
- `uvx ruff check coding/setup.py coding/tests/test_setup.py`
- `uv run ty check coding/setup.py coding/tests/test_setup.py`
- `uv run pytest coding/tests/test_setup.py -k "legacy_agents_core_block or python_cache"`
- `uvx ruff check coding/.agent_core/harness/src/utils/listing.py coding/.agent_core/harness/src/commands/log/list.py coding/.agent_core/harness/src/commands/memory/list.py coding/.agent_core/harness/src/commands/spec/list.py coding/.agent_core/harness/src/commands/task/list.py coding/.agent_core/harness/src/commands/todo/list.py`
- `uv run ty check coding/.agent_core/harness/src/utils/listing.py coding/.agent_core/harness/src/commands/log/list.py coding/.agent_core/harness/src/commands/memory/list.py coding/.agent_core/harness/src/commands/spec/list.py coding/.agent_core/harness/src/commands/task/list.py coding/.agent_core/harness/src/commands/todo/list.py`
- `git diff --check`

## Key Files Affected

- `coding/.agent_core/harness/src/commands/todo/utils/context.py` - added shared `require_dev_main_repo()` guard for mutating todo commands.
- `coding/.agent_core/harness/src/commands/todo/new.py` - requires mission-control context before creating todos or touching GitHub.
- `coding/.agent_core/harness/src/commands/todo/claim.py` - requires mission-control context before resolving, claiming, committing, pushing, or closing todo issues.
- `coding/.agent_core/harness/src/commands/todo/delete.py` - requires mission-control context before deleting todos.
- `coding/.agent_core/harness/src/commands/onboard/content.py` - made available-spec, open-todo, workflow-hint, next-step, and agent-instruction sections branch-aware.
- `coding/.agent_core/harness/src/commands/sync/main.py` - blocks all uncommitted changes before sync/rebase and prints successful spec-worktree rebase/push guidance.
- `coding/.agent_core/harness/src/utils/auto_update.py` - removes installed harness Python cache artifacts before auto-update skip/run decisions.
- `coding/AGENTS.md` - renamed the managed block tags to `<core_instructions>`.
- `coding/setup.py` - excludes Python cache artifacts from managed sync, removes them from the installed `.agent_core/harness` target when found, and migrates legacy AGENTS managed blocks to the new tag names.
- `AGENTS.md` - refreshed by `python -B coding/setup.py --update` so the installed project instructions use `<core_instructions>`.
- `coding/.agent_core/harness/src/utils/listing.py` - new location for shared table and date formatting helpers used by list commands.
- `coding/.agent_core/harness/src/commands/utils/listing.py` - removed old command-scoped location.
- `coding/.agent_core/harness/src/commands/{log,memory,spec,task,todo}/list.py` - imports updated to use `src.utils.listing`.
- `coding/tests/test_todo_context.py` - added coverage for dev-only todo mutation guards.
- `coding/tests/test_onboard.py` - added coverage that non-`dev` onboard output does not advertise spec/todo management commands.
- `coding/tests/test_git_sync.py` - added coverage that spec worktree sync rebases onto `origin/dev`, pushes with lease, and reports success.
- `coding/tests/test_setup.py` - added coverage that managed setup sync excludes source cache artifacts, removes installed cache artifacts, and migrates legacy AGENTS managed tags.
- `coding/tests/test_auto_update.py` - added coverage that auto-update removes installed cache artifacts even when skipped.
- `.agent_core/harness/...` - refreshed installed runtime from the coding template via `python -B coding/setup.py --update`.
- `.agent_core/logs/benjamin_van_heerden_20260522_111907_session.md` - this work log.
