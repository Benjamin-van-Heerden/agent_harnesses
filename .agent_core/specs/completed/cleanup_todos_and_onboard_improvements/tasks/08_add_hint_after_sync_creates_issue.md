---
title: Add hint after sync creates issue
status: completed
created_at: '2026-01-26T09:47:34.433671'
updated_at: '2026-01-26T10:08:35.840796'
completed_at: '2026-01-26T10:08:35.840788'
---
After 'mem sync' creates a GitHub issue for a spec (the flow showing 'Created issue #X for spec Y'), add a hint suggesting the user can assign the spec. Something like 'Hint: Run mem spec assign <slug> to start working on this spec'. Only show this when an issue was actually created during sync.

## Completion Notes

Added hint in src/commands/sync.py after the 'Sync complete!' summary. When plan.outbound_creates is non-empty (meaning GitHub issues were created for specs), shows 'Hint: To start working on a spec, run: mem spec assign <slug>' for each created spec.