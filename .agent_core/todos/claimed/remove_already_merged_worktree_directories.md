---
title: Remove already merged worktree directories
status: claimed
issue_id: 86
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/86
created_at: '2026-02-14T15:30:00.812694'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-14T15:33:57.142022'
---
In addition to pruning empty worktrees on sync we should check if the branches exist on remote (and for that matter if the corresponding spec has been 'Completed' - this means that the PR was successfully merged into dev and we can delete the worktree directories locally