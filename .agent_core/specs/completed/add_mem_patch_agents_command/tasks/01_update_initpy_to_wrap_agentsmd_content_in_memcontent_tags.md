---
title: Update init.py to wrap AGENTS.md content in MEMCONTENT tags
status: completed
created_at: '2026-01-22T09:14:43.217589'
updated_at: '2026-01-22T09:20:21.768540'
completed_at: '2026-01-22T09:20:21.768534'
---
Modify create_agents_files() in src/commands/init.py to wrap the template content in <MEMCONTENT>...</MEMCONTENT> tags when creating new AGENTS.md files. The template itself (src/templates/AGENTS.md) stays unchanged - tags are added programmatically.

## Completion Notes

Modified create_agents_files() to read template content and wrap it in <MEMCONTENT> tags before writing to AGENTS.md