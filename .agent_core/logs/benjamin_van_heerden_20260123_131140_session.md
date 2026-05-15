---
created_at: '2026-01-23T13:11:40.239761'
username: benjamin_van_heerden
---
# Work Log - Codex rules file and worktree/init improvements

## Overarching Goals

Add support for Codex/Antigravity IDE agent rules file (`.agent/rules/mem.md`) and fix several issues with worktree cleanup, user mappings, and symlink handling.

## What Was Accomplished

### Added .agent/rules/mem.md for Codex support

Added creation of `.agent/rules/mem.md` in `mem init`. Unlike other IDE rule files (CLAUDE.md, .cursorrules), this must be a regular file copy rather than a symlink because Codex/Antigravity doesn't follow symlinks.

### Fixed worktree symlink cleanup

When `mem merge` cleaned up worktrees, it was deleting symlinked directories which deleted the original content in the main repo (e.g., `.claude/`). Added `_remove_worktree_symlinks()` function that reads `symlink_paths` from config and removes symlinks before `git worktree remove` runs.

### Updated mem patch agents for .agent/rules/mem.md

Extended `patch_agents` command to also update `.agent/rules/mem.md` alongside AGENTS.md:
- Creates the file if it doesn't exist
- Updates it if content differs from AGENTS.md
- Handles legacy symlinks (removes and replaces with file)

### Updated drift detection for .agent/rules/mem.md

Extended `detect_agents_drift()` in onboard to check:
- If `.agent/rules/mem.md` doesn't exist
- If it's a symlink (which Codex can't follow)
- If its content is out of sync with AGENTS.md

### Fixed user_mappings.toml to support multiple users

Changed `create_user_mappings()` to `create_or_update_user_mappings()` which now:
- Creates file if it doesn't exist
- Adds new user if file exists but user not present
- Skips if user already mapped

This allows multiple developers to run `mem init` on the same repo.

## Key Files Affected

- `src/commands/init.py`: Added `.agent/rules/mem.md` file creation (not symlink), refactored `create_or_update_user_mappings()` to add users incrementally
- `src/commands/patch.py`: Extended `patch_agents` to update `.agent/rules/mem.md`, handle symlink-to-file conversion
- `src/commands/onboard.py`: Extended `detect_agents_drift()` to check `.agent/rules/mem.md` existence, symlink status, and content sync
- `src/utils/worktrees.py`: Added `_remove_worktree_symlinks()` to safely remove symlinks before worktree deletion

## What Comes Next

- Test the changes with a full workflow (init, patch, worktree create/cleanup)
- Consider if other IDEs need similar rule file support
