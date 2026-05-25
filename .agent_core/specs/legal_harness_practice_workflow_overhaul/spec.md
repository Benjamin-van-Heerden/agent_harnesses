---
title: Legal harness practice workflow overhaul
status: todo
assigned_to: null
issue_id: 14
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/14
branch: null
pr_url: null
created_at: '2026-05-25T15:14:18.608196'
updated_at: '2026-05-25T15:17:41.209414'
completed_at: null
last_synced_at: null
local_content_hash: null
remote_content_hash: null
---
## Overview

Rework the legal harness into a more realistic practice workspace for day-to-day legal use. The change should improve the installed legal workspace layout, client creation, matter lookup, matter metadata, onboarding context, WIP drafting space, Typst compilation, and workflow tracking.

This spec is intentionally scoped for a not-yet-distributed legal harness. Do not spend implementation effort on migration or backward compatibility for existing installed legal workspaces. The only current live user can be fixed manually if needed. New installs and updated harness behavior should assume the new layout and semantics.

The important product direction is that the lawyer speaks naturally and the agent uses the harness to keep legal state organized. The harness should make the right legal/practice state visible at the right time without exposing internal command names, paths, or file formats unless the lawyer asks.

## Goals

- Rename the lawyer-owned client hierarchy from `clients/` to `ZZ_CLIENTS/` for new legal harness installs and runtime path resolution.
- Improve client creation so natural person clients are created surname-first, with deterministic slug generation such as `Van Heerden, Benjamin` -> `van_heerden_benjamin`.
- Handle client slug collisions clearly. If a generated or requested client slug already exists, fail with guidance to add a distinguishing suffix such as location, ID hint, company, or other identifying trait. A suffix such as `pretoria` should produce slugs like `van_heerden_benjamin_pretoria`.
- Add matter metadata for physical file numbers, workflow association, and last-touch tracking.
- Significantly improve matter search/lookup so file numbers and other practical identifiers resolve intuitively.
- Add generated `.agent_core/client_matter_index.toml` state listing each client and up to two most recently touched matters, and surface this index during onboard.
- Add a root-level `WIP/` workspace with clear agent guidance for non-matter drafting, experiments, templating, styling, and workflow iteration.
- Add workflow commands and workflow state using plain TOML files under `.agent_core/practice/workflows/`.
- Make `matter focus` workflow-aware so it can show linked workflow status, active steps, blocked steps, and next actions.
- Remove emojis and box-drawing output from the legal harness for PowerShell and Windows console compatibility.
- Make Git and Typst required setup dependencies with clear Windows/macOS/Linux install guidance rather than attempting automatic installation.
- Ensure `onboard` creates a local Git checkpoint after it creates or cleans up session state. Do not keep snapshotting after every harness command unless needed for onboard.
- Add a legal harness Typst compile command that writes generated PDFs as `<source-stem>.p.pdf`, and ignore `*.p.pdf` in the legal `.gitignore`.

## Technical Approach

### Source of truth

All legal harness implementation changes belong under `legal/`. Do not edit the installed project root `.agent_core/harness` runtime by hand. There are no migration/backward-compatibility requirements for this spec.

### Workspace layout and setup

Update `legal/setup.py`, `legal/.agent_core/harness/src/config/paths.py`, docs, and tests so the client root is `ZZ_CLIENTS/` instead of `clients/`. New installs should create:

- `ZZ_CLIENTS/`
- `WIP/drafts/`
- `WIP/experiments/`

The WIP guidance should make clear that matter-specific drafts belong in the matter unless the lawyer is drafting outside a matter, experimenting with templates/styles, or testing workflows. Agents should create organized subfolders under `WIP/drafts/` or `WIP/experiments/` instead of dropping loose files into `WIP/`.

Setup must require both Git and Typst. It should check for `git --version` and `typst --version` and stop with clear install guidance if either is missing. Do not silently install dependencies. Include Windows guidance for Typst using `winget install --id Typst.Typst`, plus sensible Git guidance for Windows, macOS, and Linux.

### Windows-compatible stdout

Remove emojis and box-drawing characters from legal harness stdout/stderr and installed legal docs where they are part of command guidance. Prefer ASCII headings, separators, and tables that render correctly in PowerShell. Keep output assertive and agent-directed.

### Client creation

Rework `client new` so it supports surname-first natural person creation. The harness should be able to produce `van_heerden_benjamin` from `Van Heerden, Benjamin`. The exact command interface can be chosen during implementation, but it must support:

- explicit non-person/entity clients;
- natural person client names in surname-first display form;
- deterministic slug generation;
- an explicit suffix path for collisions;
- clear collision errors that tell the agent to ask the lawyer for a distinguishing suffix.

Do not guess distinguishing suffixes.

### Matter metadata and lookup

Extend matter status frontmatter and typed state models with:

- `physical_files: list[str]`
- `workflow: str | None`
- `last_touched_at: str | None`

Physical file numbers are arbitrary strings and may include values such as `A123/24`, `LIT-0042`, or `12-345`. They should not be forced into slug rules.

Improve matter search and resolution. Search should consider at least:

- matter directory name;
- client slug;
- client display name;
- matter type;
- matter status;
- case number;
- physical file numbers;
- tags;
- workflow slug/name.

When a search term maps to multiple matters, commands that require one matter must list the matches and stop with guidance to ask the lawyer which matter to use. `matter find <query>` should surface all matches, including matches by physical file number.

### Matter touch tracking and client matter index

Add a shared touch helper that updates `last_touched_at` on a matter whenever a harness action resolves and acts on a specific matter. The agreed rule is that these should touch the matter:

- `matter focus`
- `matter resolve`
- chronology additions
- obligation additions/updates
- matter todo creation/claiming
- matter-specific work logs
- workflow-related matter commands

Broad read-only commands such as `matter list` and broad `matter find` should not touch matters.

Generate `.agent_core/client_matter_index.toml` from matter state. Treat it as generated harness state, not lawyer-owned state. The lawyer should not edit files under `.agent_core/` directly. Onboard should rebuild or refresh the index and surface each client with up to two most recently touched matters.

### Workflows

Add a `workflow` command group. At minimum, support:

- `workflow new <name>`: creates `.agent_core/practice/workflows/<slug>.toml` with a useful commented/example structure and prints guidance for the agent on how to fill it in.
- `workflow list`: lists available workflows.
- `workflow show <workflow>`: validates and summarizes a workflow.

Use plain TOML for workflow files in this spec. Do not create a custom DSL or `.pworkflow` extension yet. A future Rust rewrite can revisit a workflow DSL.

Design the workflow model as a sequence/graph of typed steps. It should support the idea that some steps can run concurrently and some are blockers. The v1 format should be declarative and typed, for example with `[[steps]]` entries containing `id`, `title`, `kind`, `requires`, and `blocks`, plus per-kind data for todos and obligations. The exact schema can be refined during implementation, but it must be typed, validated, and easy for an agent to reason about.

Matter frontmatter should link to a workflow by slug. Matter-local workflow progress should live under the matter, likely `info/workflow.toml`, and should be machine-readable. `matter focus` should load the linked workflow and matter progress, then surface:

- the workflow name;
- completed/current/blocked steps;
- missing prerequisites;
- workflow-generated open todos/obligations where applicable;
- the next recommended action.

Avoid automatically creating risky legal obligations without clear command intent. If workflow application creates todos/obligations, the command output must make that explicit and should be covered by tests.

### Typst compilation and generated PDFs

Add a legal harness command for Typst compilation instead of relying on the agent to call `typst compile` directly. The command should compile a `.typ` source and write `<source-stem>.p.pdf`. Update `.gitignore` so `*.p.pdf` is ignored. This distinguishes harness-generated PDFs from externally added PDFs and avoids bloating Git with generated artifacts.

`matter focus` should distinguish Typst sources, generated `.p.pdf` outputs, and other PDF/source material.

### Git checkpoint behavior

The current legal harness snapshots after every command via `main.py` finalization. Change this so the required checkpoint behavior is specifically tied to onboard. `onboard` should create a Git checkpoint after it creates/cleans session logs and refreshes generated state such as the client matter index. Other commands do not need automatic checkpointing as part of this spec unless their existing behavior requires it for correctness.

## Success Criteria

- New legal setup creates `ZZ_CLIENTS/` and `WIP/` structure and no longer creates `clients/` for fresh installs.
- Legal setup fails clearly when Git or Typst is missing, with actionable install guidance including Windows Typst guidance: `winget install --id Typst.Typst`.
- Legal harness stdout/stderr used by setup, onboard, focus, and core commands is PowerShell-safe ASCII.
- `client new` supports surname-first natural person creation and deterministic slug generation, and collision handling requires an explicit distinguishing suffix.
- Matter status records support physical file numbers, workflow association, and last-touch metadata.
- `matter find` and matter resolution search across the richer matter index, including physical file numbers, and ambiguous results are surfaced clearly.
- Onboard refreshes and displays `.agent_core/client_matter_index.toml` with each client and up to two most recently touched matters.
- Matter-touching commands update `last_touched_at`; broad list/find commands do not.
- Workflow commands create/list/show validated TOML workflows under `.agent_core/practice/workflows/`.
- `matter focus` reads linked workflow state and reports workflow progress and next actions.
- Harness Typst compilation creates `.p.pdf` outputs and `.gitignore` ignores generated PDFs.
- Onboard creates a local Git checkpoint after its state changes; automatic checkpointing is not performed after every command unless deliberately retained for a specific reason and documented.
- Focused legal harness tests cover the new setup layout, dependency checks, client slug collision behavior, matter lookup by physical file number, touch/index behavior, workflow commands/focus output, compile output naming, and onboard checkpoint behavior.

## Notes

- The legal harness is not distributed yet. No migration or backwards compatibility work is required for existing `clients/` installs.
- The current live user can be manually adjusted if necessary.
- Files under `.agent_core/` are harness-managed and should not be edited directly by the lawyer.
- The workflow DSL idea is promising, but out of scope for this spec. Use TOML now and preserve a path for a future DSL/Rust implementation.
- Keep the lawyer-facing product contract: the lawyer speaks naturally, and the agent translates instructions into harness actions and plain-language summaries.
