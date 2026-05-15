---
title: Update onboard to show todos prominently
status: completed
created_at: '2026-01-23T15:35:48.193978'
updated_at: '2026-01-24T18:58:29.150146'
completed_at: '2026-01-24T18:58:29.150135'
---
Update src/commands/onboard.py to show open todos more prominently when no spec is active:

1. Move the 'OPEN TODOS' section higher in the output (after AVAILABLE SPECS, before WORK LOGS)
2. Show more detail: title, description preview (first 100 chars), issue URL
3. Add a reminder: 'Use mem todo claim "title" to mark as addressed'

The existing open_todos code can be enhanced.

## Completion Notes

Added prominent OPEN TODOS section to onboard output when no spec is active. The section appears after the AVAILABLE SPECS section and shows: title, GitHub issue link, and description preview (first 200 chars) for each open todo. Also includes helpful commands (claim, new, list). Removed the old simple todos section that appeared after work logs. When a spec IS active, todos are not shown (focus should be on spec tasks).