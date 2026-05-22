---
title: Implement legal record and bookkeeping commands
status: completed
created_at: '2026-05-21T09:49:37.736418'
updated_at: '2026-05-22T11:16:28.323410'
completed_at: '2026-05-22T11:16:28.323410'
---
Implement native commands for add deadline, log communication, record note, create todo, claim todo, create memory, and create work log. Preserve existing markdown/frontmatter formats and record-entry conventions. Deadline commands must update next_deadline on matter status based on open deadlines. Todo commands must support matter-scoped and standalone todos and move claimed todos into claimed/. Work log creation must keep the explicit-prompt behavior documented in AGENTS.md while creating the same useful TODO-filled log skeleton for the agent to complete. Add focused tests around file creation, frontmatter updates, append-only record behavior, and validation failures.

## Completion Notes

Implemented native legal record and bookkeeping CLI commands for deadline add, record communication, record note, todo new, todo claim, memory new, and log new. The commands delegate to typed state helpers, preserve markdown/frontmatter formats, append chronology records, update next_deadline on matter status, move claimed todos into claimed buckets, create memory and work-log skeletons, and print direct agent guidance. Added focused installed-harness tests covering deadline creation and date validation, communication and note record append behavior, invalid communication direction, practice and matter todo creation, invalid todo priority, todo claiming, memory creation, and work log creation. Verified focused command tests plus Ruff and ty checks on touched files.
