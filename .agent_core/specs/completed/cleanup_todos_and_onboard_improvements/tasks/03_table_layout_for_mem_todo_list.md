---
title: Table layout for mem todo list
status: completed
created_at: '2026-01-26T09:29:21.828191'
updated_at: '2026-01-26T10:03:24.823303'
completed_at: '2026-01-26T10:03:24.823298'
---
Update src/commands/todo.py list_todos() to use Rich table format like mem task list and mem spec list. Suggested columns: SLUG, TITLE, GITHUB ISSUE URL (or truncated link).

## Completion Notes

Replaced the verbose multi-line per-todo format with a clean table layout. Added _truncate() helper function. Table columns: SLUG, TITLE, STATUS, ISSUE. Added hint for 'mem todo show <slug>' command.