---
title: Implement explicit assignee assignment flow
status: todo
created_at: '2026-05-20T13:11:12.914557'
updated_at: '2026-05-20T13:11:12.914557'
completed_at: null
---
Extend spec assign with an explicit assignee option while preserving bare spec assign current-user behavior. Split assignment into reusable operations for context validation, assignee resolution, frontmatter updates, dev checkpoint commits and pushes, spec branch creation, and GitHub issue assignee sync. Remote-user assignment must create and push the spec branch but must not create a local worktree for the assigning user.