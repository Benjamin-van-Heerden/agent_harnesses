---
title: Implement memory migration
status: completed
created_at: '2026-02-11T14:59:41.034815'
updated_at: '2026-02-11T17:24:20.561756'
completed_at: '2026-02-11T17:24:20.561747'
---
Add a function _migrate_memories(mem_dir: Path, agent_rules_dir: Path) that migrates all memories from .mem/memories/ to agent_rules/memories/. For each .md file: (1) Parse frontmatter (title, created_at, updated_at). (2) Strip frontmatter, keep markdown body. (3) Derive slug from original filename (strip .md). (4) Write to agent_rules/memories/m_{slug}.md with just the markdown body (title and content).

## Completion Notes

Added _migrate_memories() to light.py. Strips frontmatter, writes title + body to agent_rules/memories/m_{slug}.md. Handles missing memories dir gracefully.