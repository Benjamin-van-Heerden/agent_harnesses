---
title: Fix init configs and files drift
status: claimed
issue_id: 63
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/63
created_at: '2026-01-26T08:55:47.874667'
claimed_by: Benjamin-van-Heerden
claimed_at: '2026-01-26T09:30:01.048414'
---
In some directories, important commands w.r.t. file creation (CLAUDE.md, .cursorrules) may not have run yet. Similarly, github tags may not have been created yet - we need a way to detect this in sync and then patch it appropriately. The key commands to compare against here is 'mem init' and it should be patched with e.g. 'mem patch init'