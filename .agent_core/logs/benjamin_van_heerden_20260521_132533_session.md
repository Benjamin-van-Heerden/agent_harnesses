---
created_at: '2026-05-21T13:25:33.703527'
username: benjamin_van_heerden
spec_slug: migrate_legal_harness_to_native_agent_core_structure
---
Work Log - Legal harness migration design decisions

## Overarching Goals

The session focused on the first research/design task for the `migrate_legal_harness_to_native_agent_core_structure` spec.

The goal was to inspect the current legacy `legal/` harness, reason from the perspective of a working lawyer, and capture a durable migration map before implementation. The discussion deliberately went beyond a mechanical directory rename. We clarified what legal-domain primitives the native harness should expose, how legacy `agent_rules/` installs should migrate, how local git snapshotting should work, and what should remain out of scope for the Python harness.

## What Was Accomplished

### Researched the legacy legal harness

Surveyed the current `legal/` surfaces:

- `legal/AGENTS.md`
- `legal/bash_setup.sh`
- `legal/agent_rules/commands/*.md`
- `legal/agent_rules/scripts/*.py`
- `legal/agent_rules/skeletons/*.md`
- `legal/agent_rules/docs/**`
- `legal/src/**/*.typ`

Identified the current split between markdown command playbooks, standalone Python scripts, lawyer-owned state, managed Typst reference/source files, and client/matter work product.

### Captured native design decisions

Created and expanded `.agent_core/specs/migrate_legal_harness_to_native_agent_core_structure/legal_migration_research.md`.

This file now records the decisions that should guide the next implementation session:

- Fresh legal installs should use `.agent_core/`, not `agent_rules/`.
- `legal/setup.py --update` must detect legacy `agent_rules/` installs and migrate durable state into `.agent_core/`.
- Lawyer/practice state should live under `.agent_core/practice/`.
- Client and matter state should remain top-level under `clients/`.
- Matter-scoped todos should live inside the matter directory.
- Obligations should become the core primitive; deadlines are one obligation category.
- Chronology should become typed state under `info/chronology/`.
- Obligations should be one typed file per obligation under `info/obligations/`.
- Raw/reference ingestion should stay lightweight for now.
- Typst `src/` remains partly managed and partly lawyer-evolving.
- The Python legal harness should remain local-first and solo-lawyer oriented.
- Firm/global sync, database-backed state, auth, and remote APIs are deferred to a later rewrite.
- Legal harness git behavior should be local-only post-command snapshots, with no pull, rebase, push, protected branch, PR, or GitHub workflow.

### Clarified implementation direction

The agreed next path is:

1. Build the native `legal/.agent_core/harness/` runtime foundation first.
2. Add `legal/setup.py` around that runtime.
3. Implement legacy `agent_rules/` migration during `setup.py --update`.
4. Add typed state models and path helpers.
5. Implement onboard/focus/list commands early to prove the state shape.

The note also emphasizes command stdout requirements: stdout should be clear, direct, and assertive for the agent, while lawyer-facing responses should stay human-readable and avoid exposing console commands, code, slugs, paths, or git details unless asked.

## Key Files Affected

- `.agent_core/specs/migrate_legal_harness_to_native_agent_core_structure/legal_migration_research.md`
  - Added as the durable research/design note for the first spec task.
  - Expanded into the main handoff reference for implementation.
  - Contains legacy surface mapping, managed vs lawyer-owned boundary, native runtime shape, native state proposal, obligation/chronology/todo decisions, setup migration targets, local git snapshot model, stdout/lawyer-facing language guidance, and next implementation order.

- `.agent_core/logs/benjamin_van_heerden_20260521_132533_session.md`
  - Created as the end-of-session work log.
  - This log explicitly points the next agent to the research note.

## What Comes Next

The next agent must read `.agent_core/specs/migrate_legal_harness_to_native_agent_core_structure/legal_migration_research.md` in full before editing `legal/`. That file is the reference for what to do next and captures the decisions from this session.

The `research_legal_harness_migration_decisions` task has been marked complete after explicit user approval.

The next implementation step should be the native runtime foundation:

- create `legal/.agent_core/harness/main.py`, `deps.py`, and `requirements.txt`;
- add `src/config/paths.py` and related path helpers for `.agent_core/practice/`, `.agent_core/docs/`, `clients/`, matter `info/chronology/`, `info/obligations/`, and `info/todos/`;
- add local post-command git snapshot support with no pull/rebase/push behavior;
- scaffold Typer command groups for onboard, client, matter, chronology/record, obligation, todo, memory, log, source, and lint.

After that, build `legal/setup.py` and implement native fresh install plus legacy `agent_rules/` migration during `--update`.
