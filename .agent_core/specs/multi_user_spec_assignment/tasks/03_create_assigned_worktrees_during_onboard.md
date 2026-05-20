---
title: Create assigned worktrees during onboard
status: completed
created_at: '2026-05-20T13:11:17.537166'
updated_at: '2026-05-20T14:41:26.789236'
completed_at: '2026-05-20T14:41:26.789236'
---
Add a modular onboard helper that detects active specs assigned to the authenticated GitHub user with recorded branches and no local worktree. It should create missing worktrees from the assigned remote branch after normal onboard sync and before context rendering, return typed results for output, and produce actionable failures when required remote branches are missing.

## Completion Notes

Added an onboard assigned-worktree helper that detects active specs assigned to the authenticated GitHub user, creates missing worktrees from origin/<branch> after successful sync, reports created worktrees in onboard context, and fails with actionable guidance when an assigned remote branch is missing.
