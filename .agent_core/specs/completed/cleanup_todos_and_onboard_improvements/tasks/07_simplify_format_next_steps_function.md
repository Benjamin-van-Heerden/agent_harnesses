---
title: Simplify format_next_steps function
status: completed
created_at: '2026-01-26T09:29:35.193777'
updated_at: '2026-01-26T10:07:48.930509'
completed_at: '2026-01-26T10:07:48.930503'
---
In src/commands/onboard.py format_next_steps() (lines 292-321): 1) Remove 'mem spec assign' reference (legacy command that no longer exists), 2) Remove 'Create a work log for this session' suggestion (doesn't make sense right after onboarding), 3) When no active spec, only suggest 'Create a new spec...' or 'Work on a todo...' (only mention todos if there are open todos).

## Completion Notes

Simplified format_next_steps() in src/commands/onboard.py: 1) Removed 'Or assign an existing spec: mem spec assign <slug>' suggestion, 2) Removed 'Create a work log for this session' suggestion (doesn't make sense right after onboarding), 3) When no active spec, only suggests 'Create a new spec...' and conditionally 'Work on a todo...' (only if there are open todos).