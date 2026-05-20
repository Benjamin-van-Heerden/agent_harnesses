---
created_at: '2026-05-20T15:34:40.011345'
username: benjamin_van_heerden
---
Work Log - Worktree Symlink Config Defaults And Config Patching

## Overarching Goals

Remove the nonsensical `.agent_core/docs/data` default from worktree symlink configuration, make the `symlink_paths` field documentation clear enough for installed projects, and add a reliable setup/update path for patching config comments without clobbering project-specific values.

## What Was Accomplished

### Updated symlink defaults and guidance

- Changed the coding harness default `[worktree].symlink_paths` from `[".agent_core/docs/data", ".claude"]` to `[".claude"]`.
- Updated generated config comments to explain that symlink paths are project-root relative paths symlinked from the main checkout into spec worktrees.
- Made the guidance explicit that every configured path is automatically added to `.gitignore` and must be safe to keep untracked.
- Added examples for common development-only paths such as `.env`, `.claude`, `.venv`, `node_modules`, and `deps`, with caution around manifest and lock files such as `pyproject.toml`, `package.json`, and `bun.lock`.

### Added onboard-time gitignore enforcement

- Added a runtime `src/utils/gitignore.py` helper that derives ignore entries from the typed project config.
- Wired onboard to validate/load config before sync and ensure all configured symlink paths have both file and directory forms in `.gitignore`.
- Added test coverage that verifies onboard adds a configured `.env` symlink path to `.gitignore`.

### Added setup/update config comment patching

- Added a narrow config patching helper to `coding/setup.py` and `coding/setup_support/upsert_config.py`.
- The patcher inserts the managed comment block above `[worktree].symlink_paths` for already-installed harness configs.
- It preserves the existing configured `symlink_paths` list rather than resetting it to the default.
- It replaces the old one-line legacy comment when present and avoids duplicating the block on repeated updates.

### Refreshed the local installed harness

- The user ran `python -B coding/setup.py --update`, which refreshed the installed `.agent_core/harness` runtime from the coding template and updated optional docs.
- The current repo config was updated to remove `.agent_core/docs/data` from `symlink_paths`.
- The current repo `.gitignore` was updated to remove stale `.agent_core/docs/data` worktree-symlink ignore entries.

### Verification

- Ran focused Ruff checks on touched Python files.
- Ran focused setup tests for preserved state/defaults and configured symlink ignore behavior.
- Ran `git diff --check`.

## Key Files Affected

- `coding/setup.py` - changed default symlink paths, added managed comments, and added comment patching for existing configs.
- `coding/setup_support/upsert_config.py` - mirrored setup config defaults and comment patching behavior.
- `coding/.agent_core/harness/src/config/models.py` - changed typed default for `WorktreeConfig.symlink_paths` to `[".claude"]` and expanded field description.
- `coding/.agent_core/harness/src/config/main.py` - updated generated config comments for `[worktree].symlink_paths`.
- `coding/.agent_core/harness/src/utils/gitignore.py` - new helper for deriving and applying `.gitignore` entries from configured worktree symlink paths.
- `coding/.agent_core/harness/src/commands/onboard/main.py` - loads config and ensures configured symlink paths are ignored before onboard sync/context generation.
- `coding/tests/test_setup.py` - updated expectations for the new default and added coverage for comment patching while preserving custom values.
- `coding/tests/test_onboard.py` - added coverage for onboard adding configured symlink paths to `.gitignore`.
- `.agent_core/config.toml` - removed `.agent_core/docs/data` from this repo's configured `symlink_paths` and added the new comment block.
- `.gitignore` - removed stale `.agent_core/docs/data` entries from the Agent Core worktree symlink section.
- `.agent_core/harness/...` - refreshed installed runtime from the coding template via `python -B coding/setup.py --update`.

## What Comes Next

The setup/update config patching pattern is currently narrow and only manages the `[worktree].symlink_paths` comment block. If more config fields need durable comments or migrations in the future, generalize this into an explicit config patch registry instead of adding ad hoc patches throughout `upsert_config()`.
