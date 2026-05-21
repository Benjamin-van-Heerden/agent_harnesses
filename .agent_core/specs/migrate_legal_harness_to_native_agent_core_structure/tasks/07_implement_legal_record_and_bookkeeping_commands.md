---
title: Implement legal record and bookkeeping commands
status: todo
created_at: '2026-05-21T09:49:37.736418'
updated_at: '2026-05-21T09:49:37.736418'
completed_at: null
---
Implement native commands for add deadline, log communication, record note, create todo, claim todo, create memory, and create work log. Preserve existing markdown/frontmatter formats and record-entry conventions. Deadline commands must update next_deadline on matter status based on open deadlines. Todo commands must support matter-scoped and standalone todos and move claimed todos into claimed/. Work log creation must keep the explicit-prompt behavior documented in AGENTS.md while creating the same useful TODO-filled log skeleton for the agent to complete. Add focused tests around file creation, frontmatter updates, append-only record behavior, and validation failures.