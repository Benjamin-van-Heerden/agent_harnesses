---
title: Global mem to project harness migration research
status: todo
assigned_to: Benjamin-van-Heerden
issue_id: 4
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/4
branch: dev-benjamin_van_heerden-global_mem_to_project_harness_migration_research
pr_url: null
created_at: '2026-05-19T14:15:45.015441'
updated_at: '2026-05-19T15:06:59.822118'
completed_at: null
last_synced_at: null
local_content_hash: null
remote_content_hash: null
---
## Overview

Research the migration from the existing global `mem` CLI workflows into the
project-local `.agent_core` harness model. This is intentionally a research
spec: the expected output is a markdown document that records what currently
works, what remains risky, and whether any changes are needed before using the
existing `mem migrate` command for real project migrations.

There are two migration routes to evaluate:

- `.mem -> .agent_core`, using `mem migrate --to-harness`.
- `agent_rules -> .mem`, using `mem migrate --lite-to-mem`, followed by review
  and then the `.mem -> .agent_core` route.

The existing migration implementation lives outside this repository at
`/Users/benjamin/utils/mem/src/commands/migrate.py` and
`/Users/benjamin/utils/mem/src/utils/migrate.py`. The research should treat that
code as the primary source of truth and compare its output against the current
project-local harness shape in this repository.

## Goals

- Understand the current `mem migrate --to-harness` behavior in enough detail
  to decide whether it can safely migrate legacy `.mem` projects into the
  project-local harness.
- Understand the current `mem migrate --lite-to-mem` behavior, especially how
  `agent_rules` specs and tasks are parsed back into `.mem` records.
- Identify any gaps between the global `mem` migration output and the current
  `coding/` harness expectations.
- Produce a concise markdown recommendation that can guide the first real
  migration attempts.

## Technical Approach

Review the `mem migrate` command dispatcher and its utility functions in the
global `mem` repository. Trace both migration routes from command arguments to
state writes, backup behavior, GitHub issue handling, config generation, docs
placement, and final user guidance.

For the `.mem -> .agent_core` route, inspect `run_mem_to_harness` and its helper
functions. Document the safety checks, existing-state refusal behavior, dry-run
summary, GitHub label and issue relabeling requirements, setup invocation,
state-copying behavior, config conversion, `AGENTS.md` cleanup, legacy issue
template cleanup, and `.mem.bak` backup behavior.

For the `agent_rules -> .mem` route, inspect `run_lite_to_mem` and the
conversion helpers for specs, logs, todos, memories, docs, config, and user
mappings. Pay special attention to how mem-lite spec files are interpreted into
structured `.mem` specs and tasks. Call out where deterministic parsing is
already sufficient and where AI-assisted interpretation or manual review may be
needed before continuing to `.mem -> .agent_core`.

The final output should be a markdown file in this spec directory. It should not
make broad code changes unless the research finds a concrete blocker that must
be fixed before the migration can be tested safely.

## Success Criteria

- The research markdown clearly explains both supported migration routes and
  the exact command sequence for each route.
- The markdown lists required preflight checks, including clean git state,
  remote sync expectations, GitHub token requirements, existing state refusal
  cases, and backup directories.
- The markdown identifies any harness changes that are required, or explicitly
  states that no code changes are needed if the existing migration is sufficient.
- The markdown includes manual verification steps after migration, including
  running project-local onboarding and reviewing migrated specs, tasks, todos,
  memories, logs, docs, config, and linked GitHub issues.
- Any discovered follow-up implementation work is captured as a concrete note
  rather than being implemented speculatively.

## Notes

This spec is also intended to exercise the project-local spec lifecycle itself.
Keep the research focused and avoid turning it into a broad migration rewrite.

The known command entrypoint is:

```bash
mem migrate
```

The relevant modes are:

```bash
mem migrate --to-harness
mem migrate --lite-to-mem
```
