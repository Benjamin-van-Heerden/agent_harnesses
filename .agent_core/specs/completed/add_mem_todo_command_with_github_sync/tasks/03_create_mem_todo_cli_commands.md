---
title: Create mem todo CLI commands
status: completed
created_at: '2026-01-23T15:35:32.743511'
updated_at: '2026-01-24T18:32:31.636639'
completed_at: '2026-01-24T18:32:31.636630'
---
Create src/commands/todo.py with Typer app containing three commands:

1. `new(title, description)`: Creates todo file, then creates GitHub issue with mem-todo label, stores issue_id/issue_url in frontmatter

2. `list()`: Lists all open todos showing title, created date, issue URL. Format similar to mem spec list.

3. `claim(title)`: Looks up todo by title (or slug), marks as claimed with current user and timestamp, closes GitHub issue with comment 'Claimed by @username'.

Register the todo app in main.py.

## Completion Notes

Created src/commands/todo.py with four commands: (1) 'mem todo new' - creates local todo and GitHub issue with mem-todo label, (2) 'mem todo list' - lists open todos (or all with --all flag), showing title, description preview, GitHub link, and created date, (3) 'mem todo claim' - marks todo as claimed by current user and closes linked GitHub issue, (4) 'mem todo show' - displays full todo details. All commands support partial slug matching via resolve_todo_slug_prefix(). Registered the todo_app in main.py. All commands tested and working.