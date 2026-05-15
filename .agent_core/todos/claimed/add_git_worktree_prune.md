---
title: Add git worktree prune
status: claimed
issue_id: 85
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/85
created_at: '2026-02-14T14:07:18.565042'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-02-14T15:33:51.302456'
---
Add worktree pruning to sync command, worktrees with no corresponding directory sometimes show up in the onboard output. Syncing should clear them out (sync happens at the start of onboard so the correct place to do this is in the sync command, but just need to make sure)