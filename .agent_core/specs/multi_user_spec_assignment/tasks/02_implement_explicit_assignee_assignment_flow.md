---
title: Implement explicit assignee assignment flow
status: completed
created_at: '2026-05-20T13:11:12.914557'
updated_at: '2026-05-20T14:03:33.269414'
completed_at: '2026-05-20T14:03:33.269414'
---
Extend spec assign with an explicit assignee option while preserving bare spec assign current-user behavior. Split assignment into reusable operations for context validation, assignee resolution, frontmatter updates, dev checkpoint commits and pushes, spec branch creation, and GitHub issue assignee sync. Remote-user assignment must create and push the spec branch but must not create a local worktree for the assigning user.

## Completion Notes

Extended spec assign with --assignee for assigning a spec to another mapped GitHub username, preserved the bare current-user worktree flow, validated explicit assignees through user_mappings, pushed remote assignment branches without creating a local worktree, and updated GitHub issue assignees for both flows.
