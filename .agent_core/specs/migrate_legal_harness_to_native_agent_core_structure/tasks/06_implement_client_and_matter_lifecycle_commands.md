---
title: Implement client and matter lifecycle commands
status: todo
created_at: '2026-05-21T09:49:32.035192'
updated_at: '2026-05-21T09:49:32.035192'
completed_at: null
---
Implement native commands for creating clients, creating matters, and resolving matters. Preserve existing directory and file formats: clients/<client>/profile.md, clients/<client>/matters/open/YYYYMMDD-<type>-<slug>/info/status.md, info/record.md, info/deadlines.md, raw/, reference/, and resolved matter moves. Commands should validate slugs and priorities, render skeletons through shared helpers, append appropriate record entries, update status frontmatter on resolution, and print plain next-step guidance for the agent. Add focused command tests for success paths and important validation failures.