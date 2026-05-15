---
title: Wire up the migrate command
status: completed
created_at: '2026-02-11T15:00:01.879154'
updated_at: '2026-02-11T17:26:48.762783'
completed_at: '2026-02-11T17:26:48.762776'
---
Add the @app.command() migrate() function in src/commands/light.py that orchestrates the full migration. Steps: (1) Check .mem/ exists, error if not. (2) Check agent_rules/ does NOT already exist, error if it does (prevent double migration). (3) Call _select_branches_interactive() to get branch names. (4) Call _copy_agent_rules() to create agent_rules/ structure with rendered command templates. (5) Call _migrate_specs(). (6) Call _migrate_logs(). (7) Call _migrate_memories(). (8) Call _migrate_todos(). (9) Call _migrate_docs(). (10) Call _build_agents_content() to create AGENTS.md (preserve existing user content if AGENTS.md already exists). (11) Create CLAUDE.md symlink if not present. (12) Rename .mem/ to .mem.bak/. (13) Print summary of what was migrated (counts of specs, logs, memories, todos, docs) and tell user they can delete .mem.bak/ after verifying.

## Completion Notes

Added @app.command() migrate() that orchestrates full migration: checks preconditions, prompts for branches, creates agent_rules/ structure, runs all migration functions (specs, logs, memories, todos, docs), creates AGENTS.md + CLAUDE.md symlink, renames .mem/ to .mem.bak/, prints summary with counts.