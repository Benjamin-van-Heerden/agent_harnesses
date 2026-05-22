---
title: Scaffold legal harness runtime foundation
status: completed
created_at: '2026-05-21T09:49:11.717744'
updated_at: '2026-05-21T15:44:00.704151'
completed_at: '2026-05-21T15:44:00.704151'
---
Create legal/.agent_core/harness with main.py, deps.py, requirements.txt, and the src/ package layout expected of a native Agent Core harness. Add config/path modules for resolving project root, state root, harness root, legal docs/profile directories, clients, matter state, memories, logs, todos, skeletons/templates, and Typst source. Add shared error handling and markdown/frontmatter utilities. The runtime should use Typer command composition, keep main.py small, and avoid importing command modules before dependency checks.

## Completion Notes

Added the native legal harness runtime foundation under legal/.agent_core/harness. The runtime now has main.py, deps.py, requirements.txt, a Typer composition root, registered command groups for onboard, client, matter, deadline, obligation, record, todo, memory, log, and lint, typed config models and TOML loading, expanded path helpers for .agent_core/practice, .agent_core/docs, clients, matter status/chronology/obligations/todos/raw/reference paths, Typst source roots, and legacy functions/templates roots. Added shared harness error handling, markdown/frontmatter utilities, and local post-command git snapshot support. Added focused tests covering installed runtime command registration, paths/config commands, onboard execution, and markdown/frontmatter round-trip behavior. Verified with uv run pytest legal/tests/test_setup.py, uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py, and uv run ty check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py.
