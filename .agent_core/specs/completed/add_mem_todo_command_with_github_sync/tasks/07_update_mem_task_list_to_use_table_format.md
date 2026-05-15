---
title: Update mem task list to use table format
status: completed
created_at: '2026-01-24T19:18:05.037261'
updated_at: '2026-01-24T19:19:17.383525'
completed_at: '2026-01-24T19:19:17.383519'
---
Update src/commands/task.py list_tasks_cmd() to display tasks in a table format instead of the current list view.

Columns:
- slug: task slug (filename without .md)
- status: todo/completed
- body: truncated preview of task body (keep it short so table stays aligned)
- amendments: bool (Yes/No) indicating if task has ## Amendments section

This provides better visual overview of all tasks at a glance.

## Completion Notes

Implemented table format for mem task list with columns: SLUG, STATUS, AMEND (Yes/No), BODY (truncated preview). Added _has_amendments() helper to detect ## Amendments sections. Removed --verbose flag since 'mem task show' will be used for full details. Updated hints to reference the new show command.