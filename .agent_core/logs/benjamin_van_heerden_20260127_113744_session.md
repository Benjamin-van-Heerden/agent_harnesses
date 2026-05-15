---
created_at: '2026-01-27T11:37:44.129258'
username: benjamin_van_heerden
---
# Work Log - Fix feature branch desync and improve slug resolution

## Overarching Goals

Address the todo "Fix feature branch desync after rebase onto origin/dev" (GitHub issue #68) and improve slug prefix resolution to prefer active/open items over archived/completed ones.

## What Was Accomplished

### 1. Fixed feature branch desync after rebase
In `src/commands/sync.py`, added a force push with lease after successfully rebasing a feature branch onto `origin/dev`. This keeps the remote branch in sync after commit hashes change due to rebase, preventing push rejections when the user later tries to push new commits.

```python
# After successful rebase, force push with lease to update remote
subprocess.run(
    ["git", "push", "--force-with-lease"],
    cwd=cwd,
    capture_output=True,
    text=True,
)
# Don't fail if push fails - remote branch might not exist yet
```

### 2. Updated slug resolution to prefer active/open items

**Todos** (`src/utils/todos.py`): `resolve_todo_slug_prefix()` now prefers open todos over claimed ones. When there are multiple matches but only one is open, it resolves to the open one.

**Specs** (`src/utils/specs.py`): `resolve_spec_slug_prefix()` now prefers active (root) specs over completed/abandoned ones. When there are multiple matches but only one is in the root directory, it resolves to the active one.

**Tasks** (`src/utils/tasks.py`): `resolve_task_slug_prefix()` now prefers todo tasks over completed ones. When there are multiple matches but only one has status "todo", it resolves to that one.

### 3. Display full todo descriptions in onboard
Removed the 200-character truncation limit for todo descriptions in `src/commands/onboard.py`. Todos now display their full body content with proper indentation.

### 4. Simplified onboard hint message
Shortened the verbose todo claim hint message in `format_next_steps()`.

## Key Files Affected

- `src/commands/sync.py` - Added force push with lease after feature branch rebase
- `src/utils/todos.py` - Updated `resolve_todo_slug_prefix()` to prefer open todos
- `src/utils/specs.py` - Updated `resolve_spec_slug_prefix()` to prefer active specs
- `src/utils/tasks.py` - Updated `resolve_task_slug_prefix()` to prefer todo tasks
- `src/commands/onboard.py` - Removed todo description truncation, simplified hint message

## What Comes Next

No immediate follow-up needed. The todo has been claimed and closed (GitHub issue #68).
