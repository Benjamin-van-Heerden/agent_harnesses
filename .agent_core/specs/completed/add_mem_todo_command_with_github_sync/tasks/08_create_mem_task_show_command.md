---
title: Create mem task show command
status: completed
created_at: '2026-01-24T19:18:11.087177'
updated_at: '2026-01-24T19:30:25.767641'
completed_at: '2026-01-24T19:30:25.767635'
---
Create a new 'mem task show <partial_slug>' command in src/commands/task.py.

The command should:
- Accept a partial slug (like other show commands) with slug prefix resolution
- Display full task details: title, status, created_at, updated_at
- Show the complete body content including any ## Amendments section
- Support --spec option to specify which spec (defaults to active spec)

Similar pattern to 'mem spec show' and 'mem todo show' commands.

## Completion Notes

Implemented mem task show command with partial slug matching via resolve_task_slug_prefix(). Command displays full task details including title, slug, status, spec, filename, timestamps, and complete body with amendments. Shows helpful commands for completing/amending. Handles ambiguous slugs with clear error messages listing matches.