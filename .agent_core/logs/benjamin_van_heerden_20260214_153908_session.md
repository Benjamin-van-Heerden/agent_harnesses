---
created_at: '2026-02-14T15:39:08.896185'
username: benjamin_van_heerden
---
# Work Log - Add worktree pruning and cleanup to sync

## Overarching Goals

Add automatic worktree housekeeping to the sync command so stale worktree entries and lingering worktree directories for completed/merged specs are cleaned up. This ensures agents always get a clean view during onboard.

## What Was Accomplished

### Added `prune_and_cleanup_worktrees()` to sync command

Added a new function in `src/commands/sync.py` that runs as step 2b during sync (after protected branch sync, before git pull/rebase). It performs three operations:

1. **`git worktree prune`** — removes stale worktree entries where the backing directory no longer exists. Counts removals by comparing worktree list before/after.

2. **Worktree directory removal** — for each remaining non-main worktree, extracts the spec slug from the branch name (`dev-{user}-{slug}`) and checks:
   - If the spec status is `completed` or `abandoned` (via `specs.get_spec()` which searches root/completed/abandoned dirs)
   - If the branch no longer exists on remote (deleted after PR merge)
   
   If either condition is true, force-removes the worktree and deletes the local branch.

3. **Empty base dir cleanup** — removes the `project-worktrees/` directory if empty (handles `.DS_Store`).

### Wiring

- Runs with the same guard as `sync_protected_branches` — only from main repo, skipped in worktrees
- Output: `✓ Worktrees: pruned N stale, removed N completed` (only shown when work was done)

### Todos claimed

- Claimed and closed "Add git worktree prune" (GitHub issue #85)
- Claimed and closed "Remove already merged worktree directories" (GitHub issue #86)

## Key Files Affected

- `src/commands/sync.py` — Added `prune_and_cleanup_worktrees()` function, added imports from `src.utils.worktrees`, wired into sync flow as step 2b

## What Comes Next

No immediate follow-up needed. The remaining open todo is "Add introspect codebase command" (issue #84).
