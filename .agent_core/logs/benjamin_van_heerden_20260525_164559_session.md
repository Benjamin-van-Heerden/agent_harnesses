---
created_at: '2026-05-25T16:45:59.766342'
username: benjamin_van_heerden
spec_slug: legal_harness_practice_workflow_overhaul
---
Work Log - Legal Harness Practice Workflow Overhaul

## Overarching Goals

Completed the active `legal_harness_practice_workflow_overhaul` spec. The work reworked the legal harness into a more realistic practice workspace with Windows-safe output, required Git/Typst dependencies, `ZZ_CLIENTS/` and WIP layout, richer client and matter handling, workflow support, Typst compilation, matter touch/index state, and onboard-only git checkpointing.

## What Was Accomplished

### Setup, Output, And Layout

- Legal setup now requires `git --version` and `typst --version` before install/update, with clear Windows/macOS/Linux install guidance including `winget install --id Typst.Typst`.
- Runtime dependencies now require both Git and Typst with actionable stderr guidance.
- Removed emoji and box-drawing characters from legal harness-owned command output and installed placeholder guidance.
- New installs now create `ZZ_CLIENTS/` instead of `clients/`.
- New installs create `WIP/drafts/`, `WIP/experiments/`, and `WIP/README.md` guidance for non-matter drafting and experiments.

### Client And Matter Workflows

- `client new` now supports surname-first natural person names like `Van Heerden, Benjamin`, generating deterministic slugs like `van_heerden_benjamin`.
- Entity/non-person clients are explicitly supported, with `--slug` for lawyer-provided slugs and `--suffix` for collision-safe generated slugs.
- Matter status frontmatter and typed state now support `physical_files`, `workflow`, `last_touched_at`, `case_number`, and `tags`.
- Matter lookup is now case-insensitive and searches matter directory name, client slug, client display name, matter type/status, case number, physical file numbers, tags, and workflow.
- Ambiguous single-matter resolution lists all matching matters and tells the agent to ask the lawyer which matter to use.

### Touch Tracking, Workflows, Typst, And Git

- Added `touch_matter()` and wired it into matter focus, matter resolve, chronology additions, obligation creation, matter todo creation/claiming, and matter-specific work logs.
- Added generated `.agent_core/client_matter_index.toml` and onboard display of each client with up to two recent matters.
- Added TOML workflow support under `.agent_core/practice/workflows/`, including `workflow new`, `workflow list`, `workflow show`, and `workflow link`.
- `matter focus` now surfaces linked workflow state, including completed/current/blocked steps, missing prerequisites, next action, and workflow todo/obligation guidance.
- Added `compile <source.typ>` harness command, which writes generated PDFs as `<source-stem>.p.pdf`.
- Generated legal `.gitignore` now ignores `*.p.pdf`, and `matter focus` distinguishes Typst sources, generated `.p.pdf` outputs, and other PDFs.
- Removed automatic git checkpointing from the harness process finalizer. Onboard now explicitly creates the local git checkpoint after refreshing generated/session state.

### Verification

- `uv run pytest legal/tests/test_setup.py -q` passed after each task, ending with 20 passing tests.
- Targeted `uv run ty check ...` passed for edited Python files.
- Targeted `uvx ruff check ...` passed for edited Python files.

## Key Files Affected

- `legal/setup.py`: required external dependency checks, new workspace directories, WIP guidance, `*.p.pdf` gitignore entry, workflow state directory creation.
- `legal/AGENTS.md`: added explicit rule that legal Typst compilation must go through the harness compile command, not direct `typst compile`.
- `legal/.agent_core/harness/main.py`: registered workflow and compile command groups; removed finalizer checkpointing.
- `legal/.agent_core/harness/deps.py`: required Git and Typst at runtime.
- `legal/.agent_core/harness/src/config/paths.py`: added `ZZ_CLIENTS`, WIP, workflow, and generated index paths.
- `legal/.agent_core/harness/src/state/clients.py`: surname-first slug generation, entity slug generation, suffix handling, collision guidance.
- `legal/.agent_core/harness/src/state/matters.py`: richer metadata parsing, broad matter lookup, ambiguity guidance, `touch_matter()`.
- `legal/.agent_core/harness/src/state/client_index.py`: generated client/matter index state and TOML writer.
- `legal/.agent_core/harness/src/state/workflows.py`: typed workflow parsing, validation, progress, linking, and focus support.
- `legal/.agent_core/harness/src/state/typst.py`: Typst compile wrapper and `.p.pdf` output path handling.
- `legal/.agent_core/harness/src/commands/*`: client, matter, onboard, workflow, and compile command behavior updates.
- `legal/.agent_core/practice/templates/status.md`: added physical files and workflow sections.
- `legal/optional_docs/legal_harness_function.md`: updated legal workflow guidance for new layout, lookup, touch/index, workflows, and compile behavior.
- `legal/tests/test_setup.py`: expanded behavior coverage for each completed task, while removing brittle exact AGENTS wording assertions after feedback.

## Errors and Barriers

- Several focused test failures were fixed during implementation: stale expected client type after switching to explicit entity clients, workflow-linked matter focus failing when the workflow slug did not exist, and a git status assertion that expected a nested untracked file instead of Git's directory-level `ZZ_CLIENTS/` report.
- The user correctly objected to brittle exact wording assertions added around `AGENTS.md`. Those assertions were removed. The source rule remains in `legal/AGENTS.md`, while behavioral coverage stays on actual compile command behavior, `.gitignore`, and focus classification.

## What Comes Next

- The legal test suite should get its own follow-up spec. `legal/tests/test_setup.py` is now a large catch-all integration file; future work should split it into focused files such as setup, clients, matters, workflows, Typst compile, onboard, and git behavior, and replace brittle text assertions with stable behavior contracts.
