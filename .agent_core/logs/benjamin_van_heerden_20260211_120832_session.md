---
created_at: '2026-02-11T12:08:32.928190'
username: benjamin_van_heerden
---
# Work Log - Add memory system and mem light commands

## Overarching Goals

Address two open todos: add a memory system to mem, and add `mem light init` / `mem light update` commands for lightweight mem usage in external projects.

## What Was Accomplished

### Memory System (`mem memory`)

Added a full CRUD memory system as a new primitive in mem. Memories are short, atomic notes about patterns, conventions, or preferences stored as markdown files with YAML frontmatter in `.mem/memories/`.

- Added `MemoryFrontmatter` Pydantic model and `create_memory_frontmatter()` factory to `src/models.py`
- Added `memories_dir` property to `env_settings.py`
- Created `src/utils/memories.py` with CRUD operations: `create_memory`, `get_memory`, `list_memories`, `update_memory`, `delete_memory`, `resolve_memory_slug`
- Created `src/commands/memory.py` with 5 subcommands: `new`, `list`, `show`, `update`, `delete` — all with git commit+push after mutations
- Integrated memories into `src/commands/onboard.py` — "PROJECT MEMORIES" section appears before work logs
- Updated `src/templates/mem.md` with Memories in core concepts and command reference
- Updated `src/templates/AGENTS.md` with memory guidance for agents

### Mem Light (`mem light`)

Built a lightweight, standalone version of mem for projects where full mem can't be used (e.g. consulting). Uses markdown files and git commands that agents read and execute as step-by-step instructions.

- Created `src/commands/light.py` with `init` and `update` commands
- `init` prompts for dev/prod/test branch names (defaults: `dev`/`main`/`test`), creates `agent_rules/` directory structure, renders all command files with branch names via `string.Template.safe_substitute()`, creates `AGENTS.md` with `<core_instructions>` tags, and creates `CLAUDE.md` symlink
- `update` detects branch names from existing `AGENTS.md`, overwrites command files, updates core instructions while preserving user content after `</core_instructions>`, reports what changed or "up to date"
- Replaced pseudo-scripting syntax from `$...$` to `@...@` across all command files to avoid collision with `string.Template`'s `$var` syntax
- Added `$dev_branch`, `$prod_branch`, `$test_branch` template variables to all branch references in command files and `AGENTS.md`
- Created two new command files: `c_create_todo.md` and `c_claim_todo.md`
- Updated `AGENTS.md` template with todos section, updated directory tree, and all 9 commands in the command table
- Fixed `c_create_spec.md` to have user review step before branching (was previously after)

## Key Files Affected

- `src/models.py` — Added `MemoryFrontmatter`, `create_memory_frontmatter()`
- `env_settings.py` — Added `memories_dir` property
- `src/utils/memories.py` — NEW: Memory CRUD operations
- `src/commands/memory.py` — NEW: Memory CLI commands
- `src/commands/onboard.py` — Added memories section
- `src/commands/light.py` — NEW: `mem light init` and `mem light update`
- `src/templates/mem.md` — Added memory commands and concept
- `src/templates/AGENTS.md` — Added memory guidance for agents
- `src/templates/mem_light/AGENTS.md` — Rewritten with `<core_instructions>` tags, placeholders, todos section
- `src/templates/mem_light/agent_rules/commands/*.md` — All 9 command files rewritten with `@...@` syntax and branch placeholders
- `main.py` — Registered `memory` and `light` commands

## What Comes Next

- Both todos have been claimed. All implementation is complete.
- The mem light todo mentioned reviewing the template files in comparison with full mem to see if anything should be added or removed — the memory and todo systems were added during this session.
- Could consider adding `mem light` documentation to the README.
