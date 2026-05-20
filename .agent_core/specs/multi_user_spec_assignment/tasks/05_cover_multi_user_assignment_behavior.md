---
title: Cover multi-user assignment behavior
status: todo
created_at: '2026-05-20T13:11:26.894030'
updated_at: '2026-05-20T13:11:26.894030'
completed_at: null
---
Add focused tests for the new assignment behavior. Cover current-user assignment regression, remote-user assignment with a mapped assignee, invalid explicit assignee failure, worktree creation from an existing remote branch during onboard, and stdout snippets that distinguish local assignment from remote assignment. Keep tests targeted to this workflow rather than running or expanding unrelated coverage.