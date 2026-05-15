---
created_at: '2026-03-10T13:21:19.346724'
username: benjamin_van_heerden
---
# Work Log - Overhaul mem lite to be less git-heavy

## Overarching Goals

Overhaul mem lite (todo #95) to strip out git automation and make the system simpler for small teams where git is handled manually. Commands should not auto-commit, auto-push, fetch, rebase, or manage PRs. The core value of context management across AI agent sessions is preserved.

## What Was Accomplished

### Command template rewrites

All command templates in `src/templates/mem_lite/agent_rules/commands/` were rewritten:

- **c_onboard.md** — Stripped git sync (fetch, pull, rebase, PR checks). Just warns if not on dev branch. Reads active specs (not in completed/abandoned), reads last 5 logs flat from `agent_rules/log/`.
- **c_create_spec.md** — Removed forced branching; asks user whether to use branch+PR workflow or work directly in dev. Uses `git switch -c`. Added per-task Description, Implementation Details, Key Files subsections. Added `## Completion Report` placeholder.
- **c_complete_spec.md** — No clean-tree check. Flow: check tasks → create work log → write completion report → mark completed → move to completed/ → commit. On feature branch: rebase, force-push, ask about merging. On dev: just commit.
- **c_log_work.md** — Drastically simplified to just create a file and fill it in. No modes, no directory branching, no commit/push. Added `## Spec:` linkage and `## Errors and Barriers` section.
- **c_abandon_spec.md** — Just moves spec to `spec/abandoned/`. No branch deletion or git ops.
- **c_create_memory.md** — Removed auto-commit/push.
- **c_create_todo.md** — Removed auto-commit/push.
- **c_claim_todo.md** — Removed auto-commit/push.
- **c_init_introspect_codebase.md** — Added README scanning, more detailed output structure with proportionality guidance.
- **c_merge.md** — Deleted entirely.

### AGENTS.md template

- Removed c_merge from directory tree and command table
- Updated command descriptions
- Logs described as flat in `agent_rules/log/`
- Added "Git is handled manually" note
- Feature branches described as optional

### lite.py updates

- `git checkout -b` → `git switch -c` in `init()`
- `update()` now deletes orphaned command files not present in templates
- `update()` flattens log subdirectories (moves files up, removes empty dirs)
- `_migrate_logs()` writes everything flat to `agent_rules/log/`
- `STATUS_MAP`: `merge_ready` maps to `Completed` instead of `Merge Ready`
- `_migrate_specs_from_dir()` updated to new spec format: `### {title}` (not `### Task:`), per-task `#### Description` / `#### Implementation Details` / `#### Key Files` subsections, `## Completion Report` (not `## Completion Report and Documentation` + `# Final Review`)

## Key Files Affected

- `src/templates/mem_lite/agent_rules/commands/c_onboard.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_create_spec.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_complete_spec.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_log_work.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_abandon_spec.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_create_memory.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_create_todo.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_claim_todo.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_init_introspect_codebase.md` — rewritten
- `src/templates/mem_lite/agent_rules/commands/c_merge.md` — deleted
- `src/templates/mem_lite/AGENTS.md` — updated
- `src/commands/lite.py` — updated init, update, migrate functions

## What Comes Next

- Testing the full flow end-to-end in a real project (init, onboard, create spec, complete spec, etc.)
- Verify `mem light update` correctly handles the transition for existing installations (orphan removal, log flattening)
- Verify `mem light migrate` produces correctly formatted specs from old `.mem/` data
- Close todo #95
