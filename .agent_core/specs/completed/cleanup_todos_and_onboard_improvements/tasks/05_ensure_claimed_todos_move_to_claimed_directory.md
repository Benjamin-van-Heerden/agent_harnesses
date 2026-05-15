---
title: Ensure claimed todos move to claimed directory
status: completed
created_at: '2026-01-26T09:29:34.192470'
updated_at: '2026-01-26T10:05:57.553342'
completed_at: '2026-01-26T10:05:57.553334'
---
Check src/utils/todos.py claim_todo() function. Ensure claimed todos are moved from .mem/todos/ to .mem/todos/claimed/ subdirectory (similar to how completed specs move to .mem/specs/completed/). Create the claimed directory if it doesn't exist.

## Completion Notes

Updated src/utils/todos.py: 1) Added _get_claimed_dir() helper function, 2) Modified _get_todo_file() to check both open and claimed directories, 3) Updated list_todos() to search both directories, 4) Updated resolve_todo_slug_prefix() to search both directories, 5) Modified claim_todo() to move the todo file to .mem/todos/claimed/ subdirectory after marking it claimed.