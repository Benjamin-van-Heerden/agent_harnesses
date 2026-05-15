---
title: Implement todo migration
status: completed
created_at: '2026-02-11T14:59:47.345843'
updated_at: '2026-02-11T17:25:17.109181'
completed_at: '2026-02-11T17:25:17.109172'
---
Add a function _migrate_todos(mem_dir: Path, agent_rules_dir: Path) that migrates all todos. For open todos in .mem/todos/*.md (top-level only): (1) Parse frontmatter (title, status, created_at, etc). (2) Build mem light format: '# {title}\n\n**Status:** open\n**Created:** {created_at}\n\n{body}'. (3) Derive slug from filename. (4) Write to agent_rules/todos/t_{slug}.md. For claimed todos in .mem/todos/claimed/*.md: same but status='claimed', include '**Claimed:** {claimed_at}'. Write to agent_rules/todos/claimed/t_{slug}.md.

## Completion Notes

Added _migrate_todos() to light.py. Open todos to todos/t_{slug}.md with status open, claimed todos to todos/claimed/t_{slug}.md with status claimed and claimed_at date. Strips frontmatter, writes mem light format.