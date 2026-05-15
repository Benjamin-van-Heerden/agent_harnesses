---
created_at: '2026-02-07T15:40:42.955036'
username: benjamin_van_heerden
---
# Work Log - Fix worktree sync, untracked files blocking sync, and duplicate spec names

## Overarching Goals

Fix three issues discovered during multi-user collaboration where one user works from a worktree:
1. `mem sync` / `mem onboard` fails from worktrees because `sync_protected_branches` tries to checkout `dev` which is already checked out in the main repo
2. `mem sync` fails after `mem spec new` because untracked `.mem/` files are treated as "uncommitted changes"
3. Duplicate spec names cause a hard error instead of being handled gracefully

## What Was Accomplished

### Skip protected branch sync in worktrees

Added `is_worktree` check before calling `sync_protected_branches` in the sync command. Worktrees cannot checkout protected branches (`dev`/`test`/`main`) because they're already checked out in the main repo. This is fine — worktrees only need `origin/dev` (fetched in the next step) for rebasing their feature branch.

### Ignore untracked files in uncommitted changes checks

Changed both `has_uncommitted_changes_in_dir()` and `has_uncommitted_changes()` to use `git status --porcelain --untracked-files=no`. Untracked files (like a freshly created spec directory) don't interfere with checkout or rebase, so they shouldn't block sync. The existing sync flow already handles committing `.mem/` changes via `git_commit_and_push` after executing the sync plan.

### Handle duplicate spec names

Changed `create_spec()` to append a random 3-character hex suffix (e.g. `do_something_81b`) when a slug already exists, instead of raising a `ValueError`. Also fixed `spec.py:new()` to derive the slug from the actual created file path (`spec_file.parent.name`) instead of recomputing it from the title, so the output messages show the correct (possibly suffixed) slug.

## Key Files Affected

- `src/commands/sync.py` - Added `is_worktree` import; skip `sync_protected_branches` when in worktree; changed both uncommitted changes functions to use `--untracked-files=no`
- `src/utils/specs.py` - `create_spec()` now appends random hex suffix on duplicate instead of raising error
- `src/commands/spec.py` - `new()` derives slug from created file path instead of recomputing from title

## What Comes Next

No immediate follow-up needed. These are standalone fixes. The collaborator should be able to run `mem onboard` and `mem sync` from their worktree without issues.
