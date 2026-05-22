---
created_at: '2026-05-22T13:29:13.089290'
username: benjamin_van_heerden
spec_slug: migrate_legal_harness_to_native_agent_core_structure
---
Work Log - Complete native legal harness migration

## Overarching Goals

Complete the migration of the legal harness from the legacy `agent_rules` command/script surface to the native Agent Core structure, while refining the legal-domain primitives so the system is suitable for real legal practice use rather than a mechanical port.

## What Was Accomplished

### Native legal primitives

Reworked the command and state model around a smaller set of primitives: clients, matters, chronology, obligations, todos, memories, work logs, and Typst drafting assets. Removed top-level `deadline` and `record` commands and replaced them with `obligation add deadline` and `chronology add ...` subcommands. Deadlines now store as obligation records under `info/obligations/deadline`, and matter history stores as typed chronology events under `info/chronology/<kind>`.

### Matter lifecycle and focused context

Implemented native client and matter lifecycle commands, including matter creation, resolution, lookup, focus, and unparsed raw-file listing. `matter focus` now acts as a deterministic matter-level mini-onboard, surfacing status, recent chronology, open obligations, matter todos, drafts, PDFs, raw/reference files, and unparsed material.

### Todo namespaces and onboard output

Moved global todos to `.agent_core/todos` and kept matter-scoped todos under each matter's `info/todos`. Onboard now surfaces global and matter todos together, grouped by scope, and does not output blank todo sections or todo-specific instructions when no todos exist. Onboard output was reformatted with sections, separators, emojis, and tables where useful.

### Runtime-managed frontmatter and docs

Added typed frontmatter models and updated markdown helpers so frontmatter is managed by the harness runtime rather than interpolated by templates. Reworked templates to be body-only where appropriate.

Replaced the large installed Typst core-doc behavior with a better docs layout: compact legal harness docs are installed under `.agent_core/docs`, the detailed Typst reference lives under `.agent_docs`, and default/reference docs now use a coding-style optional docs flow with `setup.py docs list/add/update`.

### Legacy retirement and auto-update

Removed the legacy `legal/agent_rules` tree and `legal/bash_setup.sh`. Added legal harness auto-update support on onboard, following the coding harness pattern with `update_interval_days` and `AGENT_CORE_SKIP_AUTO_UPDATE`.

### Verification

Updated and expanded `legal/tests/test_setup.py` to cover install/update behavior, legacy migration, lifecycle commands, chronology/obligation/todo commands, onboard log cleanup, optional docs commands, and the removal of legacy command surfaces. The focused verification suite passed: `uv run pytest legal/tests/test_setup.py`, `uvx ruff check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py`, and `uv run ty check legal/setup.py legal/.agent_core/harness legal/tests/test_setup.py`.

## Key Files Affected

- `legal/setup.py`: native install/update flow, optional docs commands, managed docs refresh, old doc cleanup, `.agent_docs` install, and legacy migration.
- `legal/AGENTS.md`: reduced to short bootstrap/onboard instructions.
- `legal/optional_docs/legal_harness_function.md`: rewritten as the legal harness operating model with action triggers, memory guidance, and primitive boundaries.
- `legal/optional_docs/legal_harness_typst_basic_reference.typ` and `legal/optional_docs/legal_harness_typst_soft_typesystem_and_house_rules.typ`: renamed managed/default docs.
- `legal/.agent_docs/typst_detailed_reference.typ`: large Typst reference moved out of `.agent_core/docs`.
- `legal/.agent_core/harness/main.py`: registered native `chronology` and `obligation` surfaces; removed `deadline` and `record`.
- `legal/.agent_core/harness/src/commands/chronology/main.py`: added typed chronology add/list commands.
- `legal/.agent_core/harness/src/commands/obligation/main.py`: added obligation add/list commands with deadline as a subtype.
- `legal/.agent_core/harness/src/commands/matter/main.py`: added lifecycle commands and deterministic matter focus output.
- `legal/.agent_core/harness/src/commands/onboard/main.py`: added auto-update, work-log creation/cleanup, formatted context output, required doc separators, and grouped todo surfacing.
- `legal/.agent_core/harness/src/commands/todo/main.py`: updated global and matter todo listing/creation/claim behavior.
- `legal/.agent_core/harness/src/state/chronology.py`, `obligations.py`, `todos.py`, `matters.py`, `logs.py`, `memories.py`, `clients.py`: native state helpers and typed frontmatter handling.
- `legal/.agent_core/harness/src/models/frontmatter.py`: typed frontmatter models.
- `legal/.agent_core/harness/src/utils/auto_update.py` and `legal/.agent_core/harness/update.py`: legal auto-update support.
- `legal/tests/test_setup.py`: comprehensive tests for native install/update, command behavior, docs, and legacy retirement.

## What Comes Next

The spec is complete. Further refinements to the legal harness should happen ad hoc or in follow-up specs, especially around deeper legal matter workflows once the harness sees real practice use.
