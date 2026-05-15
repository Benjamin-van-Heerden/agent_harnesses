---
title: Fix init configs and files drift detection
status: completed
created_at: '2026-01-26T09:29:33.697660'
updated_at: '2026-01-26T10:04:51.768892'
completed_at: '2026-01-26T10:04:51.768886'
---
In src/commands/sync.py, add detection for missing CLAUDE.md symlink, missing .cursorrules symlink, and missing GitHub labels (mem-spec, mem-todo, status labels). Alert user during sync if drift is detected so they know to run 'mem init' or fix manually.

## Completion Notes

Added check_init_drift() function to src/commands/sync.py that checks for: 1) Missing CLAUDE.md symlink, 2) Missing .cursorrules symlink, 3) Missing GitHub labels (mem-spec, mem-todo, mem-status:*). The drift check runs at the end of sync (step 8) and displays warnings with a hint to run 'mem init' to fix issues.