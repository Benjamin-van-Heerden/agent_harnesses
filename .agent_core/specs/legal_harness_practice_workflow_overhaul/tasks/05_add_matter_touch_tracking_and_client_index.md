---
title: Add matter touch tracking and client index
status: completed
created_at: '2026-05-25T15:15:54.957780'
updated_at: '2026-05-25T16:03:10.362317'
completed_at: '2026-05-25T16:03:10.362317'
---
Add a shared touch helper that updates matter last_touched_at whenever a harness action acts on a specific matter: matter focus, matter resolve, chronology additions, obligation additions/updates, matter todo creation/claiming, matter-specific work logs, and workflow-related matter commands. Broad matter list/find commands must not touch matters. Generate .agent_core/client_matter_index.toml from matter state and refresh it during onboard. Onboard must surface each client with up to two most recently touched matters. Treat the index as generated harness state, not lawyer-owned state. Add focused tests for touch behavior, index contents, and onboard display.

## Completion Notes

Added shared touch_matter helper that updates matter last_touched_at and wired it into matter focus, matter resolve, chronology additions, obligation creation, matter todo creation/claiming, and matter-specific work logs. Broad matter find/list remain non-touching. Added generated .agent_core/client_matter_index.toml state with typed index entries and TOML serialization, refreshed it during onboard, and surfaced each client with up to two recent matters. Updated legal workflow docs and focused tests for touch behavior, index contents, and onboard display. Verified with uv run pytest legal/tests/test_setup.py -q, uv run ty check on edited touch/index files and tests, and uvx ruff check on edited files.
