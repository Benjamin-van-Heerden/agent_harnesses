---
title: Research mem to project harness migration path
status: completed
created_at: '2026-05-19T14:17:34.552037'
updated_at: '2026-05-20T09:29:51.270545'
completed_at: '2026-05-20T09:29:51.270545'
---
Research the existing mem migrate --to-harness path in /Users/benjamin/utils/mem/src/utils/migrate.py. Document what it currently does for .mem to .agent_core migration, including state copying, config conversion, docs placement, AGENTS cleanup, GitHub issue relabeling, safety checks, backup behavior, dry-run output, and setup invocation. The deliverable is a markdown section explaining whether any agent_harnesses changes are needed before using this route and what manual verification steps should be run.

## Completion Notes

Researched the current mem migrate --to-harness implementation against the current coding harness shape. Added .agent_core/specs/global_mem_to_project_harness_migration_research/migration_research.md with the .mem to .agent_core route behavior, safety checks, dry-run and GitHub relabeling behavior, docs and state placement, backup behavior, and manual verification checklist. Identified branch handling as the main blocker: current mem conversion does not emit [branches].dev, installs the stale bundled mem harness instead of current coding/setup.py, and should gate non-dry-run migration to the resolved legacy dev branch with a clean, origin-synced worktree before real migrations.
