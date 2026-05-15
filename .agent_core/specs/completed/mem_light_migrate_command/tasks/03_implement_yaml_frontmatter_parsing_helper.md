---
title: Implement YAML frontmatter parsing helper
status: completed
created_at: '2026-02-11T14:59:20.602256'
updated_at: '2026-02-11T17:20:24.966278'
completed_at: '2026-02-11T17:20:24.966269'
---
Add a helper function (e.g. _parse_frontmatter(content: str) -> tuple[dict, str]) to light.py that splits a markdown file with YAML frontmatter (delimited by --- lines) into the frontmatter dict and the body string. Use yaml.safe_load for parsing. This is needed by all migration steps (specs, logs, memories, todos) since .mem/ files use YAML frontmatter but mem light files use plain markdown.

## Completion Notes

Reused existing parse_frontmatter from src/utils/markdown.py rather than duplicating. Added import to light.py.