---
created_at: '2026-01-27T16:15:41.878894'
username: benjamin_van_heerden
---
# Work Log - Remove .cursorrules file support

## Overarching Goals

Remove the `.cursorrules` file from mem's initialization and drift detection. The file is no longer needed and should be cleaned up from existing projects.

## What Was Accomplished

### Removed .cursorrules creation from init

Updated `create_agents_files()` in `src/commands/init.py` to no longer create the `.cursorrules -> AGENTS.md` symlink during `mem init`. The function now only creates:
- `AGENTS.md` (main file)
- `CLAUDE.md -> AGENTS.md` (symlink)

### Updated drift detection in sync

Changed `check_init_drift()` in `src/commands/sync.py` to detect when `.cursorrules` **exists** (previously warned when it was missing). The warning message now reads: "Deprecated .cursorrules file exists (should be removed)"

### Updated patch init to remove .cursorrules

Changed `patch_init()` in `src/commands/patch.py` to **remove** the `.cursorrules` file if it exists, rather than creating it. Uses `cursorrules_file.unlink()` to delete the file.

## Key Files Affected

- `src/commands/init.py` - Removed `.cursorrules` creation from `create_agents_files()`
- `src/commands/sync.py` - Changed `check_init_drift()` to warn if `.cursorrules` exists
- `src/commands/patch.py` - Changed `patch_init()` to remove `.cursorrules` instead of creating it

## What Comes Next

The changes are ready to be committed. After committing, running `mem patch init` on projects with existing `.cursorrules` files will remove them.
