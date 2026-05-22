---
created_at: '2026-05-22T11:19:07.272057'
username: benjamin_van_heerden
---
Work Log - Mission Control Todo Guards And Spec Rebase Messaging

## Overarching Goals

Tighten the coding harness around the intended branch roles: `dev` is mission control for project management, non-`dev` non-spec branches should not advertise or allow spec/todo management actions, and spec worktree onboarding should make its automatic `origin/dev` rebase behavior explicit.

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

### Verification

Verification completed:

- `uvx ruff check` on edited harness and test files.
- `uv run ty check` on edited harness and test files.
- `uv run pytest coding/tests/test_todo_context.py`
- `uv run pytest coding/tests/test_git_sync.py -k sync_git_state`
- `uv run pytest coding/tests/test_onboard.py -k non_dev_branch`
- `git diff --check`

## Key Files Affected

- `coding/.agent_core/harness/src/commands/todo/utils/context.py` - added shared `require_dev_main_repo()` guard for mutating todo commands.
- `coding/.agent_core/harness/src/commands/todo/new.py` - requires mission-control context before creating todos or touching GitHub.
- `coding/.agent_core/harness/src/commands/todo/claim.py` - requires mission-control context before resolving, claiming, committing, pushing, or closing todo issues.
- `coding/.agent_core/harness/src/commands/todo/delete.py` - requires mission-control context before deleting todos.
- `coding/.agent_core/harness/src/commands/onboard/content.py` - made available-spec, open-todo, workflow-hint, next-step, and agent-instruction sections branch-aware.
- `coding/.agent_core/harness/src/commands/sync/main.py` - blocks all uncommitted changes before sync/rebase and prints successful spec-worktree rebase/push guidance.
- `coding/tests/test_todo_context.py` - added coverage for dev-only todo mutation guards.
- `coding/tests/test_onboard.py` - added coverage that non-`dev` onboard output does not advertise spec/todo management commands.
- `coding/tests/test_git_sync.py` - added coverage that spec worktree sync rebases onto `origin/dev`, pushes with lease, and reports success.
- `.agent_core/logs/benjamin_van_heerden_20260522_111907_session.md` - this work log.

## What Comes Next

Propagate the coding harness template update into installed runtimes after the change is committed and pushed.
