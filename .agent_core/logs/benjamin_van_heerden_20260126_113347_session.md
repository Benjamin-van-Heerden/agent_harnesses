---
created_at: '2026-01-26T11:33:47.406496'
username: benjamin_van_heerden
---
# Work Log - Fix worktree symlink corruption

## Overarching Goals

Investigate and fix two issues:
1. Symlink corruption in worktree flow - `.claude` directory was becoming corrupted (self-referential symlink) after spec completion and merge
2. Claimed todos not being moved to `claimed/` subdirectory

## What Was Accomplished

### Root Cause Analysis - Symlink Corruption

Traced through the worktree lifecycle to identify the corruption:
- `_create_worktree_symlinks()` creates absolute symlinks (e.g., `.claude -> /abs/path/to/main/.claude`)
- Git stores symlinks by their target path
- When worktree branch is rebased/merged to dev, the symlink gets committed
- When checked out in the main repo, the symlink becomes self-referential

The fix: ensure all `symlink_paths` from config are gitignored so symlinks never get committed.

### Root Cause Analysis - Todos Not Moved

The todos were claimed at 09:30 (commit `2ca6086`) but the "move to claimed directory" functionality was only merged at 10:24 (commit `c711df0`). The spec that added the feature was the same spec that claimed those todos - so they were claimed with the old code. This was a one-time timing issue, not a bug in current code.

### Implementation - Auto-gitignore Symlink Paths

Added `ensure_symlink_paths_gitignored()` function to `src/commands/sync.py`:
- Reads `worktree.symlink_paths` from `.mem/config.toml`
- Checks each path against existing `.gitignore` entries
- Appends any missing entries with a comment header
- Normalizes paths (strips trailing slashes) to avoid duplicates

Called at the start of `mem sync` (step 0, before any git operations).

## Key Files Affected

- `src/commands/sync.py` - Added `ensure_symlink_paths_gitignored()` function and integrated into sync command
- `.gitignore` - `.claude` was automatically added during testing

## What Comes Next

The symlink issue is now prevented going forward. Any path in `worktree.symlink_paths` will automatically be gitignored on next sync.

For existing projects with corrupted symlinks, manual cleanup may be needed:
1. Remove the corrupted symlink/directory from git: `git rm -r .claude` (if tracked)
2. Recreate as proper directory: `mkdir .claude`
3. Run `mem sync` to ensure it's gitignored
