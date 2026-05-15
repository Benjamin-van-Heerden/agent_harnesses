---
created_at: '2026-01-26T10:21:32.395400'
username: benjamin_van_heerden
spec_slug: cleanup_todos_and_onboard_improvements
---
# Work Log - Cleanup todos and onboard improvements

## Overarching Goals

Address all open todos related to the todo system and improve the onboard output for better usability. This spec consolidated several small fixes and improvements including git operations after todo creation, table layouts, drift detection, todo organization, and sync command UX improvements.

## What Was Accomplished

### 1. Removed legacy `mem spec activate` references
- Updated `src/commands/init.py` to suggest `mem spec assign` instead of `activate`
- Updated `main.py` docstring to remove activate/deactivate references
- Updated `README.md` Quick Start and Commands sections

### 2. Git add/commit/push after todo creation
- Modified `src/commands/todo.py` to call `git_commit_and_push()` after creating a todo
- Keeps remote in sync immediately when new todos are created

### 3. Table layout for `mem todo list`
- Replaced verbose multi-line output with clean table format
- Columns: SLUG, TITLE, STATUS, ISSUE
- Added `_truncate()` helper function

### 4. Init configs drift detection
- Added `check_init_drift()` function in `src/commands/sync.py`
- Checks for missing CLAUDE.md and .cursorrules symlinks
- Optionally checks GitHub labels (skipped during sync for performance)

### 5. Claimed todos move to claimed directory
- Updated `src/utils/todos.py` with `_get_claimed_dir()` helper
- Modified `claim_todo()` to move files to `.mem/todos/claimed/`
- Updated `list_todos()` and `resolve_todo_slug_prefix()` to search both directories

### 6. Moved todos section lower in onboard output
- Relocated OPEN TODOS section to appear after RECENT WORK LOGS
- Now appears before SUGGESTED NEXT STEPS

### 7. Simplified `format_next_steps()` function
- Removed "create a work log" suggestion (doesn't make sense right after onboard)
- Removed `mem spec assign` suggestion when no active spec
- Only suggests working on todos if there are open todos

### 8. Added hint after sync creates issue
- Shows `mem spec assign <slug>` hint when sync creates GitHub issues for specs

### 9. Investigated and optimized sync performance
- Profiled sync command: ~96% of time is GitHub API/git network operations
- Optimized drift check to skip label API call, saving ~0.7s
- Added "Plan ready (X action(s) to perform)" message after build_sync_plan

## Key Files Affected

- `src/commands/init.py` - Updated next steps hint
- `src/commands/onboard.py` - Moved todos section, simplified format_next_steps()
- `src/commands/sync.py` - Added check_init_drift(), hint after issue creation, plan ready message
- `src/commands/todo.py` - Added git commit/push, table layout for list
- `src/utils/todos.py` - Added claimed directory support
- `main.py` - Updated docstring
- `README.md` - Updated commands documentation

## What Comes Next

All 9 tasks in this spec are complete. The spec is ready to be completed and merged.
