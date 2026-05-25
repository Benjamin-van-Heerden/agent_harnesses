---
title: Verify multi-user coding harness update behavior
status: open
issue_id: 19
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/19
created_at: '2026-05-25T18:06:28.456067'
claimed_by: null
claimed_at: null
---
Verify and document the multi-user behavior for coding/ harness auto-updates when .agent_core/config.toml [harness].last_updated_at is changed by one user. Expected behavior may already be fine: the updating user commits/pushes the refreshed installed runtime and timestamp, and the next user's onboard pulls/rebases those changes before deciding whether an auto-update is due. Confirm there is no stale-update gap, especially around dirty worktrees, unpushed updates, and whether setup/update commits all required runtime changes with the timestamp.