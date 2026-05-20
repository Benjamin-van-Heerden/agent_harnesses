---
title: Create assigned worktrees during onboard
status: todo
created_at: '2026-05-20T13:11:17.537166'
updated_at: '2026-05-20T13:11:17.537166'
completed_at: null
---
Add a modular onboard helper that detects active specs assigned to the authenticated GitHub user with recorded branches and no local worktree. It should create missing worktrees from the assigned remote branch after normal onboard sync and before context rendering, return typed results for output, and produce actionable failures when required remote branches are missing.