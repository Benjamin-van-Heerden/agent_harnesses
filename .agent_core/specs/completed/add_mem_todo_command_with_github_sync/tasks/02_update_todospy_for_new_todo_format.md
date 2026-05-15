---
title: Update todos.py for new todo format
status: completed
created_at: '2026-01-23T15:35:24.321415'
updated_at: '2026-01-24T18:27:09.022153'
completed_at: '2026-01-24T18:27:09.022147'
---
Update src/utils/todos.py to support the new frontmatter fields: status (open/claimed), claimed_by, claimed_at. Update create_todo() to accept these fields. Add claim_todo() function that sets claimed_by to username and claimed_at to current timestamp. Ensure list_todos() can filter by status.

## Completion Notes

Updated todos.py with new format per spec: (1) Changed 'completed_at' field to 'claimed_by' and 'claimed_at' fields, (2) Renamed complete_todo() to claim_todo() which takes a claimed_by username parameter, (3) Added create_todo() parameters for issue_id/issue_url to support creating todos with GitHub links, (4) Added get_open_todos() helper, (5) Added get_todo_by_title() and get_todo_slug_by_title() helpers for finding todos by title. All functions import and work correctly.

## Completion Notes

Updated todos.py with: (1) Changed 'completed_at' to 'claimed_by'/'claimed_at' fields, (2) Renamed complete_todo() to claim_todo(slug, claimed_by), (3) Added create_todo() parameters for issue_id/issue_url, (4) Added get_open_todos(), get_todo_by_title(), get_todo_slug_by_title() helpers, (5) Added resolve_todo_slug_prefix() for git-style partial slug matching like in specs.py.