---
created_at: '2026-01-26T16:47:54.329667'
username: benjamin_van_heerden
---
# Work Log - Add mem patch init command

## Overarching Goals

Add a lightweight `mem patch init` command to fix init drift issues detected by `mem sync`, without requiring a full `mem init` reinitialization.

## What Was Accomplished

### Added `mem patch init` command

Created a new subcommand under `mem patch` that fixes common init drift issues:
- Missing `CLAUDE.md` symlink (creates symlink to `AGENTS.md`)
- Missing `.cursorrules` symlink (creates symlink to `AGENTS.md`)
- Missing `pre-merge-commit` hook (creates the hook)

The command:
- Uses the existing `check_init_drift()` function from sync to detect issues
- Supports `--dry-run` flag to preview fixes
- Falls back gracefully when drift is detected but no automatic fix is available

### Updated sync output

Changed the hint message from `mem init` to `mem patch init` when drift is detected during sync.

## Key Files Affected

- `src/commands/patch.py` - Added `patch_init()` command function
- `src/commands/sync.py` - Updated drift warning message to suggest `mem patch init`

## What Comes Next

No immediate follow-up needed. The feature is complete and working.
