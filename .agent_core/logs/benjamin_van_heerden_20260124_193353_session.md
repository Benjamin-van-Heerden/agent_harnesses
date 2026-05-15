---
created_at: '2026-01-24T19:33:53.013869'
username: benjamin_van_heerden
spec_slug: add_mem_todo_command_with_github_sync
---
# Work Log - Implement mem todo command with GitHub sync

## Overarching Goals

Implement a formal `mem todo` command system for managing standalone work items that sync bidirectionally with GitHub issues. This allows tracking work items that aren't tied to a specific spec, with visibility during onboarding.

## What Was Accomplished

### 1. Added mem-todo label to mem init
- Updated `src/commands/init.py` to create `mem-todo` label (blue, 1D76DB) alongside `mem-spec` label during project initialization
- Fixed `tests/test_init.py` to use Pydantic validation instead of legacy string pattern matching

### 2. Updated todos.py for new todo format
- Changed `completed_at` field to `claimed_by` and `claimed_at` fields
- Renamed `complete_todo()` to `claim_todo(slug, claimed_by)`
- Added `create_todo()` parameters for `issue_id` and `issue_url`
- Added helper functions: `get_open_todos()`, `get_todo_by_title()`, `get_todo_slug_by_title()`
- Added `resolve_todo_slug_prefix()` for git-style partial slug matching

### 3. Created mem todo CLI commands
- Created `src/commands/todo.py` with four commands: `new`, `list`, `claim`, `show`
- `new` creates local todo and GitHub issue with `mem-todo` label
- `claim` marks todo as claimed and closes GitHub issue with comment
- Registered `todo_app` in `main.py`

### 4. Updated sync for mem-todo label
- Sync creates todos from ALL non-spec GitHub issues (not just mem-todo labeled) for visibility
- The `mem-todo` label is used for outbound sync (identifying todos created via CLI)
- Claiming any todo closes its linked GitHub issue

### 5. Updated onboard to show todos prominently
- Added prominent OPEN TODOS section when no spec is active
- Shows title, GitHub issue link, and description preview for each todo
- Updated `format_spec_detail()` to show full task details for pending tasks (not just titles)

### 6. Updated mem spec new reminder
- Changed reminder from multi-line instruction to simpler: "If this spec addresses any open todos, claim them"

### 7. Updated mem task list to table format
- Changed from list view to table with columns: SLUG, STATUS, AMEND (Yes/No), BODY (truncated)
- Added `_has_amendments()` helper function
- Fixed error message to remove "mem spec activate" terminology (doesn't exist)

### 8. Created mem task show command
- Added `resolve_task_slug_prefix()` to `src/utils/tasks.py`
- Created `show` command with partial slug matching
- Displays full task details including amendments section
- Shows helpful commands for completing/amending

### 9. Updated mem.md template
- Added Todos to core concepts
- Added Todos section with `mem todo new`, `mem todo list`, `mem todo claim` commands

## Key Files Affected

- `src/commands/init.py` - Added mem-todo label creation
- `src/utils/todos.py` - New todo format with claim fields, prefix resolution
- `src/commands/todo.py` - New file with todo CLI commands
- `src/commands/sync.py` - Updated to create todos from all non-spec issues
- `src/commands/onboard.py` - Added prominent OPEN TODOS section, full task details
- `src/commands/spec.py` - Updated new spec reminder about todos
- `src/commands/task.py` - Table format for list, new show command
- `src/utils/tasks.py` - Added resolve_task_slug_prefix()
- `src/templates/mem.md` - Added todo documentation
- `main.py` - Registered todo_app
- `tests/test_init.py` - Fixed to use Pydantic validation

## What Comes Next

All spec tasks are complete. The spec is ready for completion and PR creation.
