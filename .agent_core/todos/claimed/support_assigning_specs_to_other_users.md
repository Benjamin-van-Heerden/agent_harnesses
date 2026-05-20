---
title: Support assigning specs to other users
status: claimed
issue_id: 5
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/5
created_at: '2026-05-19T15:18:37.222320'
claimed_by: benjamin_van_heerden
claimed_at: '2026-05-20T13:05:23.318323'
---
Add multi-user spec assignment support to the coding harness. Bare spec assign <slug> should keep assigning to the authenticated user. Add an explicit assignee flag for assigning to another GitHub username, and require explicit assignees to exist in .agent_core/user_mappings.toml. When assigning to another person, write assignment metadata, create and push the assignment checkpoint on dev, create and push the remote spec branch, and sync GitHub issue assignment, but do not create a local worktree for the current user. On onboard, detect specs assigned to the authenticated user that do not yet have a local spec worktree and automatically create the worktree from the assigned spec branch. Keep this logic modular so it can later be exposed as a dedicated command such as spec sync-assigned if automatic onboard creation proves too invasive. Onboard output should quietly notify the user, for example: Spec XYZ was assigned to you; a worktree has been created at project-worktrees/XYZ, without disrupting the broader onboarding flow.