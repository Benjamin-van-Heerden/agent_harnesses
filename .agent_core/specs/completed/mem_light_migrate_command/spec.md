---
title: mem light migrate command
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 82
issue_url: https://github.com/Benjamin-van-Heerden/mem/issues/82
branch: dev-benjamin_van_heerden-mem_light_migrate_command
pr_url: https://github.com/Benjamin-van-Heerden/mem/pull/83
created_at: '2026-02-11T14:41:05.174497'
updated_at: '2026-02-11T17:57:47.633547'
completed_at: '2026-02-11T17:57:47.632112'
last_synced_at: '2026-02-11T15:02:41.379068'
local_content_hash: 9280a13a7b7e22b9ca37cb515dece1968f5c2ed2a450c6570c9f2812fb195107
remote_content_hash: 9280a13a7b7e22b9ca37cb515dece1968f5c2ed2a450c6570c9f2812fb195107
---
## Overview

Add a `mem light migrate` command that converts a full mem project (`.mem/`-based) into a mem light project (`agent_rules/`-based). This enables clean handoff of projects to clients/teams who don't have access to mem. All historical context (specs, tasks, logs, memories, todos, docs) is preserved in the `agent_rules/` directory structure so the receiving team can continue AI-assisted development using the instruction-file-based workflow.

## Goals

- Migrate all specs (todo, completed, abandoned) with their tasks inlined into the mem light spec format
- Migrate all work logs with correct placement (spec-specific logs under `log/{spec_slug}/`, each spec's last log as a naked log in `log/`)
- Migrate all memories with `m_` prefix naming
- Migrate all todos (open and claimed) with `t_` prefix naming
- Migrate all docs: core docs to `docs/core/`, other markdown docs to `docs/`
- Create `AGENTS.md` and `CLAUDE.md` symlink
- Rename `.mem/` to `.mem.bak/` after successful migration
- Update `c_onboard.md` template to include a "Read Core Docs" section

## Technical Approach

### 1. New command: `mem light migrate` in `src/commands/light.py`

Add a `migrate()` command to the existing `light.py` app. The command runs from a project root that has a `.mem/` directory.

### 2. Branch name selection (interactive)

Before any migration, prompt the user to select branch names:

1. Fetch remote branches with `git branch -r --format='%(refname:short)'` (strip `origin/` prefix)
2. If fewer than 3 remote branches exist, print a warning that the project should have at least main, dev, and test branches, then exit with error
3. List all remote branches and prompt for each:
   - "Which branch is your development branch?" (validate against remote branches)
   - "Which branch is your production branch?" (validate against remote branches)
   - "Which branch is your test/staging branch?" (validate against remote branches)
4. Validation: if the user types a branch name that doesn't exist on remote, show an error and re-prompt

### 3. Create `agent_rules/` structure

Reuse `_copy_agent_rules()` from `light.py` which creates all subdirectories and renders command templates. Also create `docs/core/` subdirectory (not currently in the subdirs list — add it).

### 4. Migrate specs

For each spec in `.mem/specs/` (excluding `completed/` and `abandoned/` subdirs):

1. Read the spec's `spec.md` — parse YAML frontmatter and markdown body
2. Read all task files from `specs/{slug}/tasks/` — parse each task's frontmatter and body
3. Derive filename: `s_{created_date}_{assigned_to or git_user}__{slug}.md`
   - `created_date` from frontmatter `created_at` field, formatted as `YYYYMMDD`
   - `assigned_to` from frontmatter, falling back to `git config user.name` (lowercased, spaces to underscores)
4. Build the mem light spec format:

```md
# {title}

`%% Status: {mapped_status} %%`

## Description
{spec body content — everything after frontmatter}

## Tasks

### Task: {task_title}
- [x] {task body content}  (if completed)
- [ ] {task body content}  (if todo)

{repeat for each task, ordered by filename}

## Completion Report and Documentation
To be completed on task finalization

# Final Review
To be completed on spec finalization
```

Status mapping:
- `todo` → `Draft`
- `merge_ready` → `In Progress`
- `completed` → `Completed`
- `abandoned` → `Abandoned`

5. Write to `agent_rules/spec/` for todo/merge_ready specs
6. Repeat for `specs/completed/` → `agent_rules/spec/completed/`
7. Repeat for `specs/abandoned/` → `agent_rules/spec/abandoned/`

### 5. Migrate logs

For each log file in `.mem/logs/`:

1. Parse YAML frontmatter (fields: `created_at`, `username`, `spec_slug`)
2. Derive new filename: `{YYYYMMDDHHmm}_{username}.md` (from `created_at`)
3. Strip the YAML frontmatter, keep only the markdown body
4. Determine placement:
   - If `spec_slug` is set: this log belongs to that spec
     - Group all logs per spec_slug, sort by `created_at`
     - The **last** (most recent) log for each spec goes to `agent_rules/log/` (naked — the spec-completion summary)
     - All other logs for that spec go to `agent_rules/log/{spec_slug}/`
   - If no `spec_slug`: goes to `agent_rules/log/` (naked log)

### 6. Migrate memories

For each file in `.mem/memories/`:

1. Parse YAML frontmatter (fields: `title`, `created_at`, `updated_at`)
2. Strip frontmatter, keep markdown body
3. Derive slug from filename (strip `.md`)
4. Write to `agent_rules/memories/m_{slug}.md`

### 7. Migrate todos

For each file in `.mem/todos/` (top-level, open todos):

1. Parse YAML frontmatter
2. Build mem light todo format:
```md
# {title}

**Status:** open
**Created:** {created_at}

{body content if any}
```
3. Derive slug from filename
4. Write to `agent_rules/todos/t_{slug}.md`

For each file in `.mem/todos/claimed/`:
1. Same parsing, but status = "claimed", include `claimed_at` date
2. Write to `agent_rules/todos/claimed/t_{slug}.md`

### 8. Migrate docs

- Copy all `.md` files from `.mem/docs/core/` → `agent_rules/docs/core/`
- Copy all `.md` files from `.mem/docs/` (top-level only, not subdirs) → `agent_rules/docs/`
- Skip `.mem/docs/data/` (Chroma DB) and `.mem/docs/summaries/` (AI-generated)

### 9. Create AGENTS.md and CLAUDE.md

Use `_build_agents_content()` with the user's chosen branch names. If an existing `AGENTS.md` exists, preserve its content after `</core_instructions>` (same behavior as `mem light init`). Create `CLAUDE.md` symlink if it doesn't exist.

### 10. Rename `.mem/` to `.mem.bak/`

After all migrations complete successfully, rename `.mem/` → `.mem.bak/`. Print a message telling the user they can delete `.mem.bak/` once they've verified the migration.

### 11. Update `c_onboard.md` template

Add a "Read Core Docs" section between "Read Memories" and "Read Work Logs":

```
## Read Core Docs

@tool@ List the contents in `./agent_rules/docs/core/`
@if (there are files in docs/core/)@
  @tool@ Read all files in `./agent_rules/docs/core/`
@end if@
```

### 12. Add `docs/core/` to `_copy_agent_rules()` subdirs list

The existing `_copy_agent_rules()` function creates subdirectories but doesn't include `docs/core/`. Add it to the subdirs list so both `init`, `update`, and `migrate` create it.

## Success Criteria

- Running `mem light migrate` in a project with `.mem/` produces a complete `agent_rules/` directory with all data preserved
- Specs have tasks inlined and use the mem light format with `%% Status %%` markers
- Logs are correctly split: per-spec last log is naked, others are under `log/{spec_slug}/`
- Branch name validation prevents typos (must match a remote branch)
- Migration fails gracefully if fewer than 3 remote branches exist
- `.mem/` is renamed to `.mem.bak/` after successful migration
- `c_onboard.md` template includes core docs reading
- `docs/core/` subdirectory is created by both `init` and `migrate`
- Existing `AGENTS.md` user content is preserved

## Notes

- GitHub labels (`mem-spec`, `mem-status:*`, `mem-todo`) are intentionally left alone — the receiving team can clean those up if they want
- The Chroma vector DB and AI-generated summaries are not migrated — mem light has no indexing/search capability
- The `docs/core/` directory addition to the subdirs list is a small fix that benefits `mem light init` and `mem light update` as well
- Spec frontmatter fields like `issue_id`, `issue_url`, `pr_url`, `last_synced_at`, content hashes are all dropped — they're mem-specific sync state
