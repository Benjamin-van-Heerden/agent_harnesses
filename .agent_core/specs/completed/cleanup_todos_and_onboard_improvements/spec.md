---
title: Cleanup todos and onboard improvements
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 66
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/66
branch: dev-benjamin_van_heerden-cleanup_todos_and_onboard_improvements
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/67
created_at: '2026-01-26T09:26:44.048315'
updated_at: '2026-01-26T10:24:59.530182'
completed_at: '2026-01-26T10:24:59.528175'
last_synced_at: '2026-01-26T09:33:24.564809'
local_content_hash: 28d5d50eca77285dd2e44b23a1564f9a117196a75228e4204dcb577ecf9e959b
remote_content_hash: 28d5d50eca77285dd2e44b23a1564f9a117196a75228e4204dcb577ecf9e959b
---
## Overview

Address all open todos related to the todo system and improve the onboard output for better usability. This spec consolidates several small fixes and improvements into one cohesive update.

## Goals

- Fix git add/commit/push after todo creation so remote stays in sync
- Change `mem todo list` to use table layout (like `mem spec list` and `mem task list`)
- Fix init configs and files drift detection in sync
- Ensure todos are properly organized (claimed todos moved to subdirectory)
- Remove all references to legacy `mem spec activate` command
- Improve onboard output organization and next steps suggestions

## Technical Approach

### 1. Git add/commit/push after todo creation
In `src/commands/todo.py`, after creating a todo file and GitHub issue, run git add, commit, and push with message like "Added todo: <todo_slug>".

### 2. Table layout for `mem todo list`
Update `src/commands/todo.py` `list_todos()` to use Rich table format similar to `mem task list` and `mem spec list`. Columns: SLUG, TITLE, GITHUB ISSUE (or link indicator).

### 3. Fix init configs drift
In `src/commands/sync.py`, add detection for missing CLAUDE.md, .cursorrules symlinks, and missing GitHub labels. Alert user if drift detected.

### 4. Todo organization (claimed directory)
Check `src/utils/todos.py` - ensure claimed todos are moved to `.mem/todos/claimed/` subdirectory (similar to how completed specs are moved).

### 5. Remove `mem spec activate` references
Search codebase for "activate" and "assign" references that are outdated. Key files: init.py, onboard.py, templates.

### 6. Move todos section lower in onboard output
In `src/commands/onboard.py`, move the OPEN TODOS section to appear after RECENT WORK LOGS but before SUGGESTED NEXT STEPS.

### 7. Simplify `format_next_steps()` function
In `src/commands/onboard.py:292-321`:
- Remove "mem spec assign" reference (legacy command)
- Remove "Create a work log for this session" suggestion (doesn't make sense right after onboard)
- When no active spec: suggest "Create a new spec..." or "Work on a todo..." (only if todos exist)

## Success Criteria

- Running `mem todo new` commits and pushes the new todo file
- `mem todo list` displays a formatted table
- `mem sync` detects and reports drift in init configs/files
- Claimed todos are moved to a `claimed/` subdirectory
- No references to `mem spec activate` anywhere in codebase
- Onboard output shows todos lower (after work logs)
- Next steps are concise and contextually appropriate

## Notes

This spec addresses GitHub issues #61-#65.
