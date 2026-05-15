---
title: Update sync for mem-todo label
status: completed
created_at: '2026-01-23T15:35:40.083277'
updated_at: '2026-01-24T18:51:04.322720'
completed_at: '2026-01-24T18:51:04.322714'
---
Update src/commands/sync.py to handle todos with mem-todo label:

1. In build_sync_plan(): Look for GitHub issues with 'mem-todo' label (not just non-spec issues)
2. Create local todos from GitHub issues with mem-todo label (inbound sync)
3. For todos created locally, the outbound sync is already handled by mem todo new

The existing todos_to_create logic can be adapted - just filter for mem-todo label instead of treating all non-spec issues as todos.

## Completion Notes

Updated build_sync_plan() in sync.py: non-spec GitHub issues (including both mem-todo labeled and any other issues) are synced as local todos for visibility. The mem-todo label is used for outbound sync (when creating todos via 'mem todo new'), while inbound sync captures all non-spec issues. Claiming any todo (whether from mem-todo or random issue) closes the linked GitHub issue. Updated docstring to clarify this behavior.