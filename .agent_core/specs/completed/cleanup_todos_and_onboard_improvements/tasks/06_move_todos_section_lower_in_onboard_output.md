---
title: Move todos section lower in onboard output
status: completed
created_at: '2026-01-26T09:29:34.692511'
updated_at: '2026-01-26T10:06:58.691072'
completed_at: '2026-01-26T10:06:58.691064'
---
In src/commands/onboard.py, move the OPEN TODOS section to appear after RECENT WORK LOGS but before SUGGESTED NEXT STEPS. Currently todos appear too prominently at the top.

## Completion Notes

Moved the OPEN TODOS section from inside the 'no active spec' block (where it appeared early) to after the RECENT WORK LOGS section but before the AGENT WORKFLOW HINTS section. The section still only shows when there's no active spec.