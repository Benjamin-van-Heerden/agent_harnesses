---
title: Implement client and matter lifecycle commands
status: completed
created_at: '2026-05-21T09:49:32.035192'
updated_at: '2026-05-22T10:21:43.014978'
completed_at: '2026-05-22T10:21:43.014978'
---
Implement native commands for creating clients, creating matters, and resolving matters. Preserve existing directory and file formats: clients/<client>/profile.md, clients/<client>/matters/open/YYYYMMDD-<type>-<slug>/info/status.md, info/record.md, info/deadlines.md, raw/, reference/, and resolved matter moves. Commands should validate slugs and priorities, render skeletons through shared helpers, append appropriate record entries, update status frontmatter on resolution, and print plain next-step guidance for the agent. Add focused command tests for success paths and important validation failures.

## Completion Notes

Implemented native legal lifecycle CLI commands for client new, matter new, and matter resolve. The commands delegate to typed state helpers, validate slug/client/priority failure paths through shared errors, print direct next-step guidance, and preserve the existing client/matter directory and record formats. Added focused installed-harness tests covering client creation, invalid client slug, missing client on matter creation, invalid priority, matter creation, resolution moves, status frontmatter update, record entries, and client open/resolved counts. Verified with focused pytest selection plus Ruff and ty checks on touched files.
