---
title: Add matter touch tracking and client index
status: todo
created_at: '2026-05-25T15:15:54.957780'
updated_at: '2026-05-25T15:15:54.957780'
completed_at: null
---
Add a shared touch helper that updates matter last_touched_at whenever a harness action acts on a specific matter: matter focus, matter resolve, chronology additions, obligation additions/updates, matter todo creation/claiming, matter-specific work logs, and workflow-related matter commands. Broad matter list/find commands must not touch matters. Generate .agent_core/client_matter_index.toml from matter state and refresh it during onboard. Onboard must surface each client with up to two most recently touched matters. Treat the index as generated harness state, not lawyer-owned state. Add focused tests for touch behavior, index contents, and onboard display.