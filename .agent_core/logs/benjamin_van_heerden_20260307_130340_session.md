---
created_at: '2026-03-07T13:03:40.893067'
username: benjamin_van_heerden
---
# Work Log - Fix sync ignoring archived specs and worktree removal failures

## Overarching Goals

Fix two bugs reported from a different project using mem: (1) sync repeatedly tries to re-create specs that already exist in completed/abandoned, and (2) worktree removal fails with "Directory not empty" instead of falling back gracefully.

## What Was Accomplished

### Fixed sync to skip completed/abandoned specs

Root cause: `build_sync_plan` calls `specs.get_all_specs()` which only returns active specs. Completed/abandoned specs are invisible to the `specs_by_issue_id` lookup. When a GitHub issue references an archived spec, sync can't match it, falls through to plan an INBOUND CREATE, and `execute_inbound_create` catches it with a warning — every single sync.

Additionally, the GitHub issue for the archived spec was never closed, which is why it kept appearing (sync only fetches `state="open"` issues).

Fix:
- `build_sync_plan` now builds an `archived_issue_ids` set from completed + abandoned specs
- Issues matching archived specs are skipped and queued in a new `stale_issues_to_close` plan field
- During execution, stale issues are closed on GitHub with a comment
- Added dry-run output for stale issues

### Fixed worktree removal fallback

`git worktree remove --force` can fail when the directory contains OS-generated files (`.DS_Store`, etc.). The error was caught and logged as a warning but the directory was left behind.

Fix:
- `remove_worktree` now catches the `git worktree remove` exception and falls back to `shutil.rmtree`
- Runs `git worktree prune` after manual removal to clean up stale metadata
- The leftover directory cleanup also uses `shutil.rmtree` instead of `rmdir`

## Key Files Affected

- `src/commands/sync.py` — Added `stale_issues_to_close` to `SyncPlan`, archived spec lookup in `build_sync_plan`, execution logic to close stale issues, dry-run output
- `src/utils/worktrees.py` — Added `shutil` import, wrapped `git worktree remove` in try/except with `shutil.rmtree` fallback and `git worktree prune`

## What Comes Next

- Commit and push changes to dev
- Test against the studii project to confirm the stale issue gets closed and warning disappears
