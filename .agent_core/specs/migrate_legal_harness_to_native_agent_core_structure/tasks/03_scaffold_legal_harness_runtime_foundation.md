---
title: Scaffold legal harness runtime foundation
status: todo
created_at: '2026-05-21T09:49:11.717744'
updated_at: '2026-05-21T09:49:11.717744'
completed_at: null
---
Create legal/.agent_core/harness with main.py, deps.py, requirements.txt, and the src/ package layout expected of a native Agent Core harness. Add config/path modules for resolving project root, state root, harness root, legal docs/profile directories, clients, matter state, memories, logs, todos, skeletons/templates, and Typst source. Add shared error handling and markdown/frontmatter utilities. The runtime should use Typer command composition, keep main.py small, and avoid importing command modules before dependency checks.