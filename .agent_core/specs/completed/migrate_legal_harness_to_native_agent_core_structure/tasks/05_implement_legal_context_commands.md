---
title: Implement legal context commands
status: completed
created_at: '2026-05-21T09:49:26.181624'
updated_at: '2026-05-21T16:20:51.200456'
completed_at: '2026-05-21T16:20:51.200456'
---
Implement native commands for onboard, focus matter, listing helpers, and lint. Onboard must preserve the legacy legal flow: load lawyer profile and placeholder warnings, core Typst/legal docs, workflow guidance, clients, open matters, upcoming deadlines, high/urgent matter summaries, recent logs, memories, open todos, Typst building blocks, git snapshot behavior if retained, and first-run detection. Focus matter must resolve a matter, read status/record/deadlines, survey matter-root drafts and raw/reference files, list matter-scoped todos, and print agent-facing next-step guidance. Listing and lint behavior should replace list_clients.py, list_open_matters.py, upcoming_deadlines.py, list_matter_todos.py, find_matter.py, list_unparsed.py, and lint.py with native command modules.

## Completion Notes

Implemented native legal context commands over the typed state layer. Onboard now reports profile/setup warnings, client and open-matter counts, upcoming deadlines, high-priority matters, practice todos, memories/log counts, Typst building block counts, and direct agent next-step guidance. Added client list, matter list/find/focus/list-unparsed, deadline upcoming, todo list, and lint commands. Matter focus reports status/record/deadline presence, draft/PDF counts, raw/reference counts, unparsed raw files, open todos, deadlines, and agent guidance to read relevant files before advising or drafting. Added focused installed-command tests covering the native context command surface. Verified with uv run pytest legal/tests/test_setup.py, uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py, and uv run ty check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py.
