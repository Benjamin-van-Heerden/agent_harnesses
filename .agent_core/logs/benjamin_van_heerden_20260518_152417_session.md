---
created_at: '2026-05-18T15:24:17.893404'
username: benjamin_van_heerden
---
# Work Log - Todo GitHub Sync and Function Argument Types

## Overarching Goals

Address the two open todos in the project context:

- Add explicit function argument type annotations across the coding harness.
- Restore direct GitHub issue behavior for standalone todos.

Keep implementation changes in the `coding/` harness template, preserve existing
local update/onboard changes, and verify the restored todo workflow with a
focused integration test.

## What Was Accomplished

- Ran project onboarding and read the generated onboard context.
- Reported the onboard sync warning caused by uncommitted tracked changes.
- Confirmed existing modified files from the user/update should be preserved and
  included later, not reverted.
- Added explicit function argument annotations across the coding harness files
  that were safe to edit:
  - GitHub utility wrappers.
  - Sync and merge helpers.
  - Test fixtures and test functions.
- Left the existing modified `coding/.agent_core/harness/src/commands/onboard.py`
  file untouched during the broad annotation pass, per user direction.
- Fixed PyGithub typing diagnostics by:
  - using PyGithub `NotSet` instead of `None` for omitted optional API
    parameters;
  - replacing broad `**kwargs: object` forwarding in `update_issue` with
    explicit typed keyword-only parameters.
- Restored direct todo GitHub issue behavior in the coding harness:
  - `todo new` now creates a GitHub issue first;
  - stores `issue_id` and `issue_url` in todo frontmatter;
  - commits and pushes the new todo state when the index is clean;
  - `todo claim` now rejects already-claimed todos and closes/comments on the
    linked GitHub issue when one exists.
- Added a typed `close_issue_with_comment` GitHub helper.
- Added a focused GitHub integration test proving direct `todo new` and
  `todo claim` behavior.
- Marked the `restore_github_issue_sync_for_todos` todo claimed in project
  state.
- Verified changed files with focused checks:
  - `uvx ruff check` on changed files.
  - import smoke checks for changed modules.
  - focused integration test:
    `uv run pytest coding/tests/test_github_flow.py::test_todo_new_creates_linked_issue_and_claim_closes_it`
    passed.

## Key Files Affected

- `coding/.agent_core/harness/src/utils/github.py`
- `coding/.agent_core/harness/src/commands/todo/new.py`
- `coding/.agent_core/harness/src/commands/todo/claim.py`
- `coding/.agent_core/harness/src/commands/sync/main.py`
- `coding/.agent_core/harness/src/commands/merge/utils.py`
- `coding/tests/test_github_flow.py`
- `coding/tests/conftest.py`
- `coding/tests/github_helpers.py`
- `coding/tests/test_local_commands.py`
- `coding/tests/test_migration.py`
- `coding/tests/test_onboard.py`
- `coding/tests/test_remote_migration.py`
- `coding/tests/test_setup.py`
- `coding/tests/test_worktrees.py`
- `.agent_core/todos/claimed/restore_github_issue_sync_for_todos.md`
- `.agent_core/logs/benjamin_van_heerden_20260518_152417_session.md`

Also present in the final working tree from earlier update/onboard work:

- `.agent_core/harness/src/commands/merge/into.py`
- `.agent_core/harness/src/commands/merge/pr.py`
- `.agent_core/harness/src/commands/onboard.py`
- `coding/.agent_core/harness/src/commands/onboard.py`

## What Comes Next

- Commit and push the accumulated session changes.
- The explicit function argument todo remains open until the skipped modified
  onboard file receives its final two helper parameter annotations.
- After the coding harness changes are pushed, run the normal update loop when
  ready so installed project-local harness copies receive the template changes.
