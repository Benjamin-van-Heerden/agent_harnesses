---
created_at: '2026-05-20T09:48:43.679554'
username: benjamin_van_heerden
spec_slug: global_mem_to_project_harness_migration_research
---
# Work Log - Mem Migration Research And Task Workflow Gate

## Overarching Goals

Start the first task in the `global_mem_to_project_harness_migration_research` spec, document the current `.mem -> .agent_core` migration path thoroughly, and use the ceremonial spec work to identify rough edges in the new project-local harness workflow.

## What Was Accomplished

- Reviewed the current working-tree implementation of global `mem migrate --to-harness` in `/Users/benjamin/utils/mem/src/commands/migrate.py` and `/Users/benjamin/utils/mem/src/utils/migrate.py`.
- Compared the migration output against the current `coding/` harness shape, especially config requirements, branch mapping, setup behavior, state layout, docs placement, GitHub issue relabeling, backup behavior, and final user guidance.
- Added `.agent_core/specs/global_mem_to_project_harness_migration_research/migration_research.md` with the first research section for `.mem -> .agent_core`.
- Identified branch handling as the main migration blocker: the current mem conversion preserves legacy `main` and `test`, but not `dev`; it also installs the stale bundled `mem/harnesses/mem` runtime instead of the current `coding` harness.
- Marked `Research mem to project harness migration path` complete through the harness after writing the research note.
- Used the task-completion experience to improve the `coding/` harness template: pending task rendering in onboard now includes each task slug, task list/show output exposes slugs more clearly, and `task complete` now requires the hidden `--user-gave-explicit-permission` flag before mutating state.

## Key Files Affected

- `.agent_core/specs/global_mem_to_project_harness_migration_research/migration_research.md`
- `.agent_core/specs/global_mem_to_project_harness_migration_research/tasks/01_research_mem_to_project_harness_migration_path.md`
- `coding/.agent_core/harness/src/commands/onboard/content.py`
- `coding/.agent_core/harness/src/commands/task/complete.py`
- `coding/.agent_core/harness/src/commands/task/utils/formatting.py`
- `.agent_core/logs/benjamin_van_heerden_20260520_094843_session.md`

## What Comes Next

- Continue with the remaining spec task: `Research agent_rules to mem migration path`.
- Consider propagating the `coding/` harness template changes with the setup/update flow rather than manually duplicating edits into installed `.agent_core/harness`.
- Before real migrations, update the final-use `mem migrate --to-harness` path so it writes `[branches].dev`, runs only from the resolved legacy dev branch, verifies clean origin-synced state, and installs the current `coding` harness instead of the stale bundled `mem/harnesses/mem` runtime.
