---
created_at: '2026-02-16T13:02:55.243740'
username: benjamin_van_heerden
---
# Work Log - Evaluate and fix mem lite command templates

## Overarching Goals

Critically evaluate the ordering and robustness of the mem lite agent command templates (`agent_rules/commands/c_*.md`). The commands are pseudo-scripts that guide AI agents through git-based workflows, and several had issues with operation ordering, missing failure handling, and unsafe git patterns.

## What Was Accomplished

### Rewrote c_onboard.md

- Replaced `git stash` approach with detect-and-stop: if the working tree is dirty, the agent shows the changes and stops with advice (commit or discard). No more auto-stashing.
- Removed `git add -A && git diff --staged --stat && git reset` (risky staging/unstaging) — replaced with `git status --short`, `git diff --stat`, `git diff --cached --stat`, `git ls-files --others`.
- Removed `git ls-files ':(exclude).agent_rules/*'` — too noisy, wastes context window.
- Moved open PR check from sync section to "Review Recent Activity" (informational, not sync).
- Reordered context reading: core docs before memories/todos.

### Rewrote c_create_spec.md

- Added `git fetch origin && git pull` before the wip commit/branching section so the spec branch starts from the latest remote state.
- Added a step to show the user what will be committed and get confirmation before the wip commit.
- Added failure handling on pull and push.

### Fixed c_merge.md

- Added `git fetch origin` alongside the existing `git pull`.
- Added clear failure messages throughout (merge failures, branch deletion, push).

### Rewrote c_abandon_spec.md

- Added `git fetch origin && git pull` at the start.
- Reordered: delete the branch first (fallible), then move the spec file (safe). Previously spec file was moved first, leaving a half-done state if branch deletion failed.
- Made remote branch delete non-fatal (may not exist if branch was never pushed).
- Added push failure handling.

### Rewrote c_complete_spec.md

- Added dirty tree check before rebase — asks the user what to do with uncommitted changes.
- Added incomplete tasks warning — stops and asks user to confirm if there are unchecked tasks in the spec.
- Added clear failure messages on rebase, push (`--force-with-lease`), and PR creation with common causes.

### Fixed c_log_work.md

- Removed unnecessary read of `c_create_spec.md` template (was reading the spec command template to understand spec structure, but only the spec file itself is needed).
- Removed `git diff --staged` (full diff) — kept only `--stat`. Full diff can dump huge amounts into the context window.
- Added push failure handling.

### Added git push to simple commands

- `c_claim_todo.md`, `c_create_memory.md`, `c_create_todo.md` — all were committing locally but not pushing. Added `git push` after each commit.

### Claimed todo

- Claimed and closed "Evaluate and change mem lite onboard flow" (GitHub issue #87).

## Key Files Affected

- `src/templates/mem_lite/agent_rules/commands/c_onboard.md` — full rewrite
- `src/templates/mem_lite/agent_rules/commands/c_create_spec.md` — added sync, confirmation, failure handling
- `src/templates/mem_lite/agent_rules/commands/c_merge.md` — added fetch, failure handling
- `src/templates/mem_lite/agent_rules/commands/c_abandon_spec.md` — full rewrite
- `src/templates/mem_lite/agent_rules/commands/c_complete_spec.md` — full rewrite
- `src/templates/mem_lite/agent_rules/commands/c_log_work.md` — removed unnecessary reads, added failure handling
- `src/templates/mem_lite/agent_rules/commands/c_claim_todo.md` — added git push
- `src/templates/mem_lite/agent_rules/commands/c_create_memory.md` — added git push
- `src/templates/mem_lite/agent_rules/commands/c_create_todo.md` — added git push

## What Comes Next

- The `c_init_introspect_codebase.md` command was reviewed and is clean — no changes needed.
- These templates haven't been tested on an actual mem lite project yet. Worth deploying to a real project and running through the flows to validate.
