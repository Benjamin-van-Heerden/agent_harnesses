---
title: Implement legal context commands
status: todo
created_at: '2026-05-21T09:49:26.181624'
updated_at: '2026-05-21T09:49:26.181624'
completed_at: null
---
Implement native commands for onboard, focus matter, listing helpers, and lint. Onboard must preserve the legacy legal flow: load lawyer profile and placeholder warnings, core Typst/legal docs, workflow guidance, clients, open matters, upcoming deadlines, high/urgent matter summaries, recent logs, memories, open todos, Typst building blocks, git snapshot behavior if retained, and first-run detection. Focus matter must resolve a matter, read status/record/deadlines, survey matter-root drafts and raw/reference files, list matter-scoped todos, and print agent-facing next-step guidance. Listing and lint behavior should replace list_clients.py, list_open_matters.py, upcoming_deadlines.py, list_matter_todos.py, find_matter.py, list_unparsed.py, and lint.py with native command modules.