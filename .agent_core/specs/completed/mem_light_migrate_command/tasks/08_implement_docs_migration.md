---
title: Implement docs migration
status: completed
created_at: '2026-02-11T14:59:53.386089'
updated_at: '2026-02-11T17:25:52.937185'
completed_at: '2026-02-11T17:25:52.937176'
---
Add a function _migrate_docs(mem_dir: Path, agent_rules_dir: Path) that migrates documentation files. (1) Copy all .md files from .mem/docs/core/ to agent_rules/docs/core/ (straight copy, preserve filenames). (2) Copy all .md files from .mem/docs/ top-level only (not subdirs like core/, data/, summaries/) to agent_rules/docs/. (3) Skip .mem/docs/data/ (Chroma DB) and .mem/docs/summaries/ (AI-generated) entirely.

## Completion Notes

Added _migrate_docs() to light.py. Copies core docs to docs/core/, top-level .md files to docs/. Skips data/ and summaries/ naturally by only globbing *.md at specific levels.