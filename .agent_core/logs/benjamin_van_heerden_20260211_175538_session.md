---
created_at: '2026-02-11T17:55:38.836794'
username: benjamin_van_heerden
spec_slug: mem_light_migrate_command
---
# Work Log - Implement mem light migrate command

## Overarching Goals

Implement the `mem light migrate` command that converts a full `.mem/`-based project into a mem light `agent_rules/`-based project, preserving all historical context (specs, tasks, logs, memories, todos, docs) so receiving teams can continue AI-assisted development without mem.

## What Was Accomplished

### Core infrastructure
- Added `docs/core` to subdirs list in `_copy_agent_rules()` so it's created by init/update/migrate
- Added "Read Core Docs" section to `c_onboard.md` template between "Read Memories" and "Read Work Logs"
- Reused existing `parse_frontmatter` from `src/utils/markdown.py` instead of duplicating

### Branch selection
- Added `_get_remote_branches()` to fetch remote branches with `origin/` prefix stripped
- Added `_select_branches_interactive()` with validation (minimum 3 remote branches, re-prompt on invalid input)

### Migration functions (all in `src/commands/light.py`)
- `_migrate_specs()` / `_migrate_specs_from_dir()` — Migrates active/completed/abandoned specs with tasks inlined as checkbox sections, status mapping (todo->Draft, merge_ready->In Progress, etc.), proper filenames `s_{date}_{user}__{slug}.md`
- `_migrate_logs()` — Groups by spec_slug, most recent per spec goes naked to `log/`, older ones to `log/{spec_slug}/`. Handles both old `date` and new `created_at` frontmatter formats. Filenames include seconds to avoid collisions.
- `_migrate_memories()` — Strips frontmatter, writes `# {title}\n\n{body}` to `memories/m_{slug}.md`
- `_migrate_todos()` — Open todos to `todos/t_{slug}.md`, claimed to `todos/claimed/t_{slug}.md` with `## Description` header
- `_migrate_docs()` — Core docs to `docs/core/`, top-level `.md` to `docs/`, skips `data/` and `summaries/`

### Migrate command
- `migrate()` orchestrator: checks preconditions, prompts for branches, creates agent_rules/ structure, runs all migrations, creates AGENTS.md (preserves existing user content), CLAUDE.md symlink, renames `.mem/` to `.mem.bak/`, prints summary with counts

### Post-audit fixes
- Task body in specs now preserved as multi-line content (not crammed into checkbox line)
- Todo files include `## Description` header matching mem light format
- Log filenames include seconds (`YYYYMMDDHHmmss`) to prevent collisions

### Task completion workflow streamline
- Removed the two-step pre-completion flow that caused double-summary stop-start loop
- Made `notes` a required argument on `mem task complete`
- Agent discovers `--user-gave-explicit-permission` flag organically on first task completion
- No-flag message teaches the workflow with "from the next task onward" framing
- Post-completion trailing instructions only shown when tasks remain (not on last task)
- Updated all hints across `mem.md`, `onboard.py`, and `task.py` to use `"detailed notes about what was done"`

## Key Files Affected

- `src/commands/light.py` — All migration functions and migrate command added
- `src/commands/task.py` — Streamlined task completion workflow
- `src/commands/onboard.py` — Updated task complete hint format
- `src/templates/mem.md` — Updated task complete hint format
- `src/templates/mem_light/agent_rules/commands/c_onboard.md` — Added "Read Core Docs" section

## What Comes Next

All 10 tasks for this spec are complete. The spec is ready for completion and PR creation.
