---
title: Migrate legal harness to native Agent Core structure
status: completed
assigned_to: Benjamin-van-Heerden
issue_id: 12
issue_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/issues/12
branch: dev-benjamin_van_heerden-migrate_legal_harness_to_native_agent_core_structure
pr_url: https://github.com/Benjamin-van-Heerden/agent_harnesses/pull/13
created_at: '2026-05-21T09:41:40.306345'
updated_at: '2026-05-22T13:42:05.740078'
completed_at: '2026-05-22T13:42:05.740078'
last_synced_at: null
local_content_hash: null
remote_content_hash: null
---
## Overview

Migrate the `legal/` harness from the legacy Praxis `agent_rules/` shape into the native Agent Core harness structure used by `coding/`.

The current legal harness has the right domain behavior, but the implementation shape is legacy:

- `legal/AGENTS.md` points agents at markdown playbooks in `agent_rules/commands/`.
- `legal/bash_setup.sh` is the installer/updater and fetches templates from the old `mem-lite` repository.
- Command behavior lives partly in markdown playbooks and partly in standalone scripts under `agent_rules/scripts/`.
- There is no template-level `legal/setup.py`.
- There is no project-local runtime under `legal/.agent_core/harness/`.
- There is no `src/commands/<area>/main.py` command tree, typed state layer, config layer, or command composition root.

The migration should preserve the legal harness's lawyer-facing behavior while replacing the legacy command dispatch and installer model with the same native Agent Core shape as the coding harness:

```text
legal/
  AGENTS.md
  README.md
  setup.py
  .agent_core/
    harness/
      main.py
      deps.py
      requirements.txt
      src/
        commands/
        config/
        models/
        state/
        utils/
```

This is not a cosmetic rename. The result should be an installable legal harness whose managed runtime is under `.agent_core/harness/`, whose durable client/matter/legal state is preserved on update, and whose command stdout tells the agent exactly what to read, edit, or do next.

## Goals

- Add a stdlib-only `legal/setup.py` installer/updater modeled on `coding/setup.py`.
- Add a native `legal/.agent_core/harness/` runtime with a small `main.py` composition root and Typer command groups.
- Move command behavior out of markdown-command dispatch and standalone `agent_rules/scripts/*.py` entrypoints into typed Python command modules, state modules, and utilities.
- Preserve the legal domain model: lawyer profile, core Typst docs, clients, matters, deadlines, records, todos, memories, logs, reusable Typst source, and lawyer-owned templates/assets.
- Preserve the lawyer-facing interaction contract in `legal/AGENTS.md`: the lawyer speaks naturally, the agent translates requests into harness actions, and implementation details are not exposed unless asked.
- Ensure setup/update replaces only managed harness/template files and preserves lawyer-owned state.
- Add focused tests for setup/update behavior and representative legal commands.
- Remove or deprecate the legacy `bash_setup.sh` and `agent_rules/commands`/`agent_rules/scripts` command-dispatch surface once the native runtime covers it.

## Technical Approach

Use the coding harness as the structural reference, but do not blindly copy coding-specific spec/worktree concepts. The legal harness has different state and workflows, so the reusable standard is the native harness architecture, installer/update boundary, typed state model, command composition style, dependency checks, and assertive agent-facing stdout.

### Current legacy surfaces to migrate

Installer/update:

- `legal/bash_setup.sh` creates directory structure, initializes git, manages `.gitignore`, refreshes `AGENTS.md`, creates `CLAUDE.md`, copies commands/scripts/skeletons/docs/Typst source, and preserves lawyer-owned state.
- It currently fetches from `Benjamin-van-Heerden/mem-lite`, not from this `agent_harnesses` repository.

Agent instructions:

- `legal/AGENTS.md` is the core lawyer-facing contract and should remain the first-class entrypoint.
- It currently instructs agents to read `agent_rules/commands/c_onboard.md` and run scripts directly.
- It should instead instruct agents to run `python -B .agent_core/harness/main.py onboard` and use native command groups.

Domain state:

- Lawyer/profile/docs: `agent_rules/lawyer_profile.md`, `agent_rules/docs/core/*`.
- Cross-cutting state: `agent_rules/memories/`, `agent_rules/log/`, `agent_rules/todos/claimed/`.
- Legal client state: `clients/<client>/profile.md`, `clients/<client>/matters/open/*`, `clients/<client>/matters/resolved/*`.
- Matter state: `info/status.md`, `info/record.md`, `info/deadlines.md`, `raw/`, `reference/`, matter-root `*.typ`/`*.pdf`.
- Reusable Typst source: `src/types`, `src/constants`, and future `src/functions`/`src/templates`.
- Legacy preserved locations: `functions/` and `templates/`.

Command behavior currently represented by playbooks/scripts:

- Session context: onboard, focus matter, log work, lint.
- Client/matter lifecycle: new client, new matter, resolve matter.
- Matter events: log communication, add deadline, record note, ingest raw.
- Cross-cutting state: create memory, create todo, claim todo.
- Helper/listing behavior: list clients, list open matters, upcoming deadlines, list matter todos, find matter, list unparsed files, git snapshot.

### Target runtime shape

Create legal command groups around the domain rather than preserving one file per old script name as the public API. A reasonable first target:

```text
src/commands/
  onboard/
  matter/
  client/
  deadline/
  record/
  todo/
  memory/
  log/
  lint/
```

Each command group should have a `main.py` that wires small verb files. Command files should expose focused `run(...)` functions, use Typer argument definitions, convert domain errors into `typer.Exit`, and print direct next-step guidance. Shared parsing and file operations belong in `src/state/` or `src/utils/`, not in command modules.

### State and parsing

Build typed state records for legal domain files instead of passing raw dictionaries through command code. The initial model set should cover:

- Client profile frontmatter.
- Matter status frontmatter.
- Todo frontmatter.
- Memory frontmatter.
- Work log frontmatter.
- Deadline entries.
- Matter record entries where useful.

The legacy `_lib.py` helpers are a good behavioral seed, but should be split into native modules:

- path resolution and project root detection in `src/config/paths.py`;
- skeleton/template rendering in `src/state/templates.py` or a similar focused module;
- frontmatter parsing/writing through a shared markdown/frontmatter utility;
- matter/client/todo/memory/log state APIs under `src/state/`;
- git snapshot and `.gitignore` behavior under `src/utils/`.

### Setup/update boundary

`legal/setup.py` should be stdlib-only and install from the `legal/` template in this repository, following the coding harness pattern.

On init/update it should:

- create required durable directories;
- install/refresh `.agent_core/harness/`;
- install/refresh the managed core block in `AGENTS.md`;
- create or refresh `CLAUDE.md` compatibility;
- install/refresh managed Typst support source under `src/` where appropriate;
- add new skeletons/templates without clobbering lawyer-edited skeletons unless an explicit reset mode exists;
- preserve lawyer-owned state: lawyer profile, legal context, clients, matters, memories, logs, todos, legacy functions/templates, raw/reference files, produced documents, and assets;
- manage a legal-specific `.gitignore` block;
- avoid referencing the old `mem-lite` repository.

### Onboard behavior

The native `onboard` command should produce the context the agent needs in one controlled flow. It should either print concise context directly or write a temp context file and explicitly require the agent to read it, matching the coding harness's agent-guidance pattern.

The onboard flow should preserve the legacy legal semantics:

- lawyer profile and placeholder warnings;
- core Typst/legal docs;
- command guidance or durable workflow guidance;
- clients and open matters;
- upcoming deadlines;
- high/urgent matter summaries;
- recent work logs;
- memories;
- open todos;
- available Typst building blocks;
- local git snapshot behavior if still desired for legal installs;
- first-run detection and handoff to initial setup guidance.

### Migration/deprecation

Do not delete useful legal behavior during the first pass. It is acceptable to keep legacy files temporarily while native commands are being built, but the final result should not require agents to use `python agent_rules/scripts/...` or read `agent_rules/commands/*.md` as the command source of truth.

If compatibility wrappers are retained, they should point to the native harness or be clearly marked legacy. The native path must be the documented path in `AGENTS.md`.

## Success Criteria

- A fresh legal harness install can be created with `python -B legal/setup.py` from a target directory.
- An existing legal harness install can be updated with `python -B legal/setup.py --update` without clobbering lawyer-owned state.
- Installed legal projects contain `.agent_core/harness/main.py` and can run `python -B .agent_core/harness/main.py onboard`.
- `legal/AGENTS.md` no longer directs agents to markdown command playbooks as the command source of truth.
- The main legal workflows are available as native harness commands: onboard, focus matter, client creation, matter creation/resolution, deadline creation, communication/note recording, todo creation/claiming, memory creation, work log creation, lint/listing helpers.
- Command implementations are typed, live under `legal/.agent_core/harness/src/commands/`, and delegate shared behavior to typed state/util modules.
- Managed files and lawyer-owned files have an explicit update boundary, with focused tests covering preservation.
- Focused tests cover representative command behavior and setup/update behavior.
- The old `mem-lite` dependency is removed from the legal harness installation path.

## Notes

- Keep the legal harness's product identity and lawyer-facing language unless there is a deliberate reason to rename it. The important migration is architectural.
- Use assertive command stdout. Harness commands should say what happened and what the agent must read or do next.
- Do not introduce coding-harness spec/worktree concepts into legal unless they are genuinely part of the legal workflow. The target is the native harness structure, not the coding harness domain model.
- This work should happen under `legal/`, not in the installed root `.agent_core/` runtime.
- The existing Typst reference docs are large and should be preserved as managed/reference assets unless a task explicitly changes their content.
